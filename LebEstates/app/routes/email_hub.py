import re
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, session, abort
from functools import wraps
from app.models.base import db
from app.models.email_hub import EmailTemplate, SenderIdentity, EmailFeatureConfig, DistributionList, DistributionListMember, DistributionListRule, EmailLog, EmailDraft
from app.models.users import AuditLog
from app.services.email_service import EmailService
from app.services.distribution_list_service import DistributionListService

email_hub_bp = Blueprint('email_hub', __name__, url_prefix='/control-panel/email-hub')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login_page'))
        role = session.get('role_name', '').lower()
        if role != 'admin':
            flash("Access Denied: Only administrators have permission to access this area.", "danger")
            return redirect(url_for('email_hub.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_or_employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login_page'))
        role = session.get('role_name', '').lower()
        if role not in ['admin', 'employee', 'accountant']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@email_hub_bp.route('')
@admin_or_employee_required
def dashboard():
    user_id = session.get('user_id')
    role = session.get('role_name', '').lower()
    is_admin = (role == 'admin')

    # Pagination parameters for logs
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10
    offset = (page - 1) * per_page

    # Base query for logs: Admin sees all logs, employee sees only their own
    logs_query = EmailLog.query
    if not is_admin:
        logs_query = logs_query.filter(EmailLog.createdByUserID == user_id)

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = datetime.utcnow() - timedelta(hours=24)

    # 1. Sent Today
    sent_today = logs_query.filter(EmailLog.status == 'Sent', EmailLog.createdAt >= today_start).count()

    # 2. Delivery Rate
    total_attempts = logs_query.count()
    total_sent = logs_query.filter(EmailLog.status == 'Sent').count()
    delivery_rate = round((total_sent / total_attempts * 100), 1) if total_attempts > 0 else 0.0

    # 3. Active Features
    active_features = EmailFeatureConfig.query.filter_by(enabled=True).count()

    # 4. Failures in last 24 hours
    pending_errors = logs_query.filter(EmailLog.status == 'Failed', EmailLog.createdAt >= yesterday).count()

    # Total count and paginated logs
    total_logs = logs_query.count()
    recent_logs = logs_query.order_by(EmailLog.createdAt.desc()).offset(offset).limit(per_page).all()
    total_pages = max(1, (total_logs + per_page - 1) // per_page)

    return render_template(
        'email_hub/hub.html',
        sent_today=sent_today,
        delivery_rate=delivery_rate,
        active_features=active_features,
        pending_errors=pending_errors,
        recent_logs=recent_logs,
        page=page,
        per_page=per_page,
        offset=offset,
        total_logs=total_logs,
        total_pages=total_pages,
        is_admin=is_admin
    )

# --- CONFIGURATION CENTER ---
@email_hub_bp.route('/config', methods=['GET'])
@admin_required
def config():
    features = EmailFeatureConfig.query.all()
    senders = SenderIdentity.query.all()
    templates = EmailTemplate.query.filter_by(isActive=True).all()
    dist_lists = DistributionList.query.all()

    # Split features into real-time direct automations vs background reminders
    reminder_categories = ['Reminders', 'Visit Reminders', 'Consultation Reminders', 'Payment Reminders']
    automation_features = []
    reminder_features = []

    for f in features:
        is_reminder = (
            f.category in reminder_categories or
            'Remind' in f.featureKey or
            'Overdue' in f.featureKey or
            'Feedback' in f.featureKey or
            'Survey' in f.featureKey or
            'Followup' in f.featureKey
        )
        if is_reminder:
            reminder_features.append(f)
        else:
            automation_features.append(f)

    return render_template(
        'email_hub/configs.html',
        features=features,
        automation_features=automation_features,
        reminder_features=reminder_features,
        senders=senders,
        templates=templates,
        dist_lists=dist_lists,
        is_admin=True
    )

@email_hub_bp.route('/config/save', methods=['POST'])
@admin_required
def save_configs():
    try:
        # Get list of feature IDs from form to process updates
        feature_ids = request.form.getlist('feature_ids')
        for fid in feature_ids:
            config_obj = EmailFeatureConfig.query.get(fid)
            if config_obj:
                config_obj.enabled = f"enabled_{fid}" in request.form
                config_obj.templateKey = request.form.get(f"template_{fid}")
                
                sender_id = request.form.get(f"sender_{fid}")
                config_obj.senderIdentityID = int(sender_id) if sender_id else None
                
                config_obj.replyToOverride = request.form.get(f"replyto_{fid}")
                config_obj.updatedAt = datetime.utcnow()
                config_obj.updatedByUserID = session.get('user_id')
        
        AuditLog.log_action(
            action='EDIT',
            table_name='email_feature_configs',
            record_id=0,
            description=f"Updated email feature routing configurations for {len(feature_ids)} features"
        )
        db.session.commit()
        flash('Email features configuration saved successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving configuration: {str(e)}', 'danger')
    return redirect(url_for('email_hub.config'))

@email_hub_bp.route('/sender/create', methods=['POST'])
@admin_required
def create_sender():
    display_name = request.form.get('display_name')
    from_email = request.form.get('from_email')
    reply_to = request.form.get('reply_to_email')
    is_default = 'is_default' in request.form

    if not display_name or not from_email:
        flash('Display Name and From Email are required.', 'danger')
        return redirect(url_for('email_hub.config'))

    try:
        # If set as default, unset previous default
        if is_default:
            SenderIdentity.query.update({SenderIdentity.isDefault: False})
        
        new_sender = SenderIdentity(
            displayName=display_name,
            fromEmail=from_email,
            replyToEmail=reply_to or None,
            isDefault=is_default,
            isActive=True
        )
        db.session.add(new_sender)
        db.session.flush()

        AuditLog.log_action(
            action='ADD',
            table_name='sender_identities',
            record_id=new_sender.senderIdentityID,
            description=f"Created email sender identity '{display_name}' <{from_email}>"
        )
        db.session.commit()
        flash('Sender identity created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating sender identity: {str(e)}', 'danger')
    return redirect(url_for('email_hub.config'))

@email_hub_bp.route('/sender/toggle/<int:id>', methods=['POST'])
@admin_required
def toggle_sender(id):
    sender = SenderIdentity.query.get_or_404(id)
    sender.isActive = not sender.isActive

    AuditLog.log_action(
        action='EDIT',
        table_name='sender_identities',
        record_id=id,
        description=f"{'Activated' if sender.isActive else 'Deactivated'} sender identity '{sender.fromEmail}'"
    )
    db.session.commit()
    return jsonify({'success': True, 'isActive': sender.isActive})

@email_hub_bp.route('/sender/delete/<int:id>', methods=['POST'])
@admin_required
def delete_sender(id):
    sender = SenderIdentity.query.get_or_404(id)
    try:
        AuditLog.log_action(
            action='DELETE',
            table_name='sender_identities',
            record_id=id,
            description=f"Deleted sender identity '{sender.fromEmail}'"
        )
        db.session.delete(sender)
        db.session.commit()
        flash('Sender identity deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting sender identity: {str(e)}', 'danger')
    return redirect(url_for('email_hub.config'))

@email_hub_bp.route('/sender/default/<int:id>', methods=['POST'])
@admin_required
def default_sender(id):
    sender = SenderIdentity.query.get_or_404(id)
    try:
        SenderIdentity.query.update({SenderIdentity.isDefault: False})
        sender.isDefault = True

        AuditLog.log_action(
            action='EDIT',
            table_name='sender_identities',
            record_id=id,
            description=f"Set sender identity '{sender.fromEmail}' as default system sender"
        )
        db.session.commit()
        flash(f'Sender identity "{sender.fromEmail}" is now the default sender.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error setting default sender: {str(e)}', 'danger')
    return redirect(url_for('email_hub.config'))

@email_hub_bp.route('/sender/get/<int:id>', methods=['GET'])
@admin_required
def get_sender(id):
    sender = SenderIdentity.query.get_or_404(id)
    return jsonify({
        'success': True,
        'senderIdentityID': sender.senderIdentityID,
        'displayName': sender.displayName,
        'fromEmail': sender.fromEmail,
        'replyToEmail': sender.replyToEmail or '',
        'verifiedStatus': sender.verifiedStatus or 'Verified',
        'isDefault': bool(sender.isDefault),
        'isActive': bool(sender.isActive)
    })

@email_hub_bp.route('/sender/edit/<int:id>', methods=['POST'])
@admin_required
def edit_sender(id):
    sender = SenderIdentity.query.get_or_404(id)
    
    if request.is_json:
        data = request.get_json() or {}
        display_name = data.get('display_name', '').strip()
        from_email = data.get('from_email', '').strip()
        reply_to = data.get('reply_to_email', '').strip()
        verified_status = data.get('verified_status', 'Verified').strip()
        is_default = bool(data.get('is_default', False))
        is_active = bool(data.get('is_active', True))
    else:
        display_name = request.form.get('display_name', '').strip()
        from_email = request.form.get('from_email', '').strip()
        reply_to = request.form.get('reply_to_email', '').strip()
        verified_status = request.form.get('verified_status', 'Verified').strip()
        is_default = 'is_default' in request.form
        is_active = 'is_active' in request.form

    if not display_name or not from_email:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Display Name and From Email are required.'}), 400
        flash('Display Name and From Email are required.', 'danger')
        return redirect(url_for('email_hub.config'))

    # Check for duplicate email on another sender
    existing = SenderIdentity.query.filter(
        SenderIdentity.fromEmail == from_email,
        SenderIdentity.senderIdentityID != id
    ).first()
    if existing:
        if request.is_json:
            return jsonify({'success': False, 'error': f'Sender email "{from_email}" is already in use by another profile.'}), 400
        flash(f'Sender email "{from_email}" is already used by another sender profile.', 'danger')
        return redirect(url_for('email_hub.config'))

    try:
        if is_default:
            SenderIdentity.query.update({SenderIdentity.isDefault: False})
            sender.isDefault = True
        else:
            sender.isDefault = is_default

        sender.displayName = display_name
        sender.fromEmail = from_email
        sender.replyToEmail = reply_to or None
        sender.isActive = is_active
        sender.verifiedStatus = verified_status

        AuditLog.log_action(
            action='EDIT',
            table_name='sender_identities',
            record_id=id,
            description=f"Updated sender identity #{id} '{display_name}' <{from_email}>"
        )
        db.session.commit()

        if request.is_json:
            return jsonify({'success': True, 'message': 'Sender identity updated successfully!'})
        flash(f'Sender identity "{display_name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error updating sender identity: {str(e)}', 'danger')

    return redirect(url_for('email_hub.config'))



# --- TEMPLATES MANAGEMENT ---
@email_hub_bp.route('/templates')
@admin_required
def templates_list():
    templates = EmailTemplate.query.all()
    return render_template('email_hub/templates.html', templates=templates, is_admin=True)

@email_hub_bp.route('/templates/create', methods=['GET', 'POST'])
@admin_required
def create_template():
    if request.method == 'POST':
        key = request.form.get('templateKey', '').strip().replace(' ', '_').upper()
        name = request.form.get('name')
        category = request.form.get('category', 'System')
        subject = request.form.get('subject')
        body = request.form.get('body')

        if not key or not name or not subject or not body:
            flash('All template fields are required.', 'danger')
            return render_template('email_hub/template_form.html', template=None, is_admin=True)

        existing = EmailTemplate.query.filter_by(templateKey=key).first()
        if existing:
            flash(f'Template with key {key} already exists.', 'danger')
            return render_template('email_hub/template_form.html', template=None, is_admin=True)

        try:
            new_tpl = EmailTemplate(
                templateKey=key,
                name=name,
                category=category,
                subject=subject,
                body=body,
                isActive=True,
                updatedByUserID=session.get('user_id')
            )
            db.session.add(new_tpl)
            db.session.flush()

            AuditLog.log_action(
                action='ADD',
                table_name='email_templates',
                record_id=new_tpl.templateID,
                description=f"Created email template '{name}' (Key: {key})"
            )
            db.session.commit()
            flash('Email template created successfully!', 'success')
            return redirect(url_for('email_hub.templates_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating template: {str(e)}', 'danger')

    return render_template('email_hub/template_form.html', template=None, is_admin=True)

@email_hub_bp.route('/templates/edit/<string:key>', methods=['GET', 'POST'])
@admin_required
def edit_template(key):
    template = EmailTemplate.query.filter_by(templateKey=key).first_or_404()
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        subject = request.form.get('subject')
        body = request.form.get('body')
        is_active = 'isActive' in request.form

        if not name or not subject or not body:
            flash('Name, Subject, and Body are required.', 'danger')
            return render_template('email_hub/template_form.html', template=template, is_admin=True)

        try:
            template.name = name
            template.category = category
            template.subject = subject
            template.body = body
            template.isActive = is_active
            template.updatedByUserID = session.get('user_id')
            template.updatedAt = datetime.utcnow()

            AuditLog.log_action(
                action='EDIT',
                table_name='email_templates',
                record_id=template.templateID,
                description=f"Updated email template '{name}' (Key: {key})"
            )
            db.session.commit()
            flash('Email template updated successfully!', 'success')
            return redirect(url_for('email_hub.templates_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating template: {str(e)}', 'danger')

    return render_template('email_hub/template_form.html', template=template, is_admin=True)

@email_hub_bp.route('/templates/delete/<string:key>', methods=['POST'])
@admin_required
def delete_template(key):
    template = EmailTemplate.query.filter_by(templateKey=key).first_or_404()
    try:
        AuditLog.log_action(
            action='DELETE',
            table_name='email_templates',
            record_id=template.templateID,
            description=f"Deleted email template '{template.name}' (Key: {key})"
        )
        db.session.delete(template)
        db.session.commit()
        flash('Email template deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting template: {str(e)}', 'danger')
    return redirect(url_for('email_hub.templates_list'))


# --- DISTRIBUTION LISTS ---
@email_hub_bp.route('/distribution-lists')
@admin_required
def distribution_lists():
    lists = DistributionList.query.all()
    return render_template('email_hub/distribution_lists.html', lists=lists, is_admin=True)

@email_hub_bp.route('/distribution-lists/create', methods=['POST'])
@admin_required
def create_distribution_list():
    name = request.form.get('name')
    desc = request.form.get('description')

    if not name:
        flash('List Name is required.', 'danger')
        return redirect(url_for('email_hub.distribution_lists'))

    try:
        new_list = DistributionList(name=name, description=desc, isActive=True)
        db.session.add(new_list)
        db.session.flush()

        new_rule = DistributionListRule(
            distributionListID=new_list.distributionListID,
            includeEmployees=False,
            includeAdmins=False,
            includeCustomers=False,
            onlyActiveUsers=True,
            excludeBlacklistedCustomers=True
        )
        db.session.add(new_rule)

        AuditLog.log_action(
            action='ADD',
            table_name='distribution_lists',
            record_id=new_list.distributionListID,
            description=f"Created distribution list '{name}'"
        )
        db.session.commit()
        flash('Distribution list created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating list: {str(e)}', 'danger')
    return redirect(url_for('email_hub.distribution_lists'))

@email_hub_bp.route('/distribution-lists/edit-rules/<int:id>', methods=['POST'])
@admin_required
def edit_list_rules(id):
    dl_list = DistributionList.query.get_or_404(id)
    rule = DistributionListRule.query.filter_by(distributionListID=id).first()
    if not rule:
        rule = DistributionListRule(distributionListID=id)
        db.session.add(rule)

    try:
        dl_list.description = request.form.get('description')
        rule.includeCustomers = 'include_customers' in request.form
        rule.includeEmployees = 'include_employees' in request.form
        rule.includeAdmins = 'include_admins' in request.form
        rule.onlyActiveUsers = 'only_active' in request.form
        rule.excludeBlacklistedCustomers = 'exclude_blacklisted' in request.form
        rule.manualEmailsRaw = request.form.get('manual_emails')

        AuditLog.log_action(
            action='EDIT',
            table_name='distribution_lists',
            record_id=id,
            description=f"Updated rules and configuration for distribution list '{dl_list.name}'"
        )
        db.session.commit()
        flash('List rules and description updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving rules: {str(e)}', 'danger')
    return redirect(url_for('email_hub.distribution_lists'))

@email_hub_bp.route('/distribution-lists/delete/<int:id>', methods=['POST'])
@admin_required
def delete_distribution_list(id):
    dl = DistributionList.query.get_or_404(id)
    try:
        AuditLog.log_action(
            action='DELETE',
            table_name='distribution_lists',
            record_id=id,
            description=f"Deleted distribution list '{dl.name}'"
        )
        db.session.delete(dl)
        db.session.commit()
        flash('Distribution list deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting list: {str(e)}', 'danger')
    return redirect(url_for('email_hub.distribution_lists'))

@email_hub_bp.route('/distribution-lists/member/add/<int:list_id>', methods=['POST'])
@admin_required
def add_list_member(list_id):
    email = request.form.get('email', '').strip()
    label = request.form.get('label', '').strip()
    mtype = request.form.get('member_type', 'Other')

    if not email:
        flash('Email address is required.', 'danger')
        return redirect(url_for('email_hub.distribution_lists'))

    try:
        new_member = DistributionListMember(
            distributionListID=list_id,
            email=email,
            label=label or None,
            memberType=mtype,
            isActive=True
        )
        db.session.add(new_member)
        db.session.flush()

        AuditLog.log_action(
            action='ADD',
            table_name='distribution_list_members',
            record_id=new_member.memberID,
            description=f"Added member '{email}' to distribution list ID {list_id}"
        )
        db.session.commit()
        flash('Member added to distribution list.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding list member: {str(e)}', 'danger')
    return redirect(url_for('email_hub.distribution_lists'))

@email_hub_bp.route('/distribution-lists/member/delete/<int:member_id>', methods=['POST'])
@admin_required
def delete_list_member(member_id):
    member = DistributionListMember.query.get_or_404(member_id)
    try:
        AuditLog.log_action(
            action='DELETE',
            table_name='distribution_list_members',
            record_id=member_id,
            description=f"Removed member '{member.email}' from distribution list ID {member.distributionListID}"
        )
        db.session.delete(member)
        db.session.commit()
        flash('Member removed from distribution list.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing member: {str(e)}', 'danger')
    return redirect(url_for('email_hub.distribution_lists'))

@email_hub_bp.route('/distribution-lists/resolve/<int:id>')
@admin_or_employee_required
def resolve_list_emails(id):
    emails = DistributionListService.resolve_recipients(id)
    return jsonify({'success': True, 'emails': emails, 'count': len(emails)})


# --- COMPOSER & DRAFTS ---
@email_hub_bp.route('/compose')
@admin_or_employee_required
def compose():
    role = session.get('role_name', '').lower()
    is_admin = (role == 'admin')
    drafts = EmailDraft.query.filter_by(createdByUserID=session.get('user_id')).order_by(EmailDraft.lastUpdated.desc()).all()
    templates = EmailTemplate.query.filter_by(isActive=True).all()
    dist_lists = DistributionList.query.all()
    return render_template(
        'email_hub/compose.html',
        drafts=drafts,
        templates=templates,
        dist_lists=dist_lists,
        is_admin=is_admin
    )

@email_hub_bp.route('/send', methods=['POST'])
@admin_or_employee_required
def send_email_action():
    subject = request.form.get('subject')
    body = request.form.get('body')
    recipients_raw = request.form.get('recipients_raw')
    list_ids = request.form.getlist('distribution_lists')

    # Resolve all recipients
    recipients = set()

    # 1. Manual recipients
    if recipients_raw:
        manuals = re.split(r'[,\s;\n\r]+', recipients_raw)
        for email in manuals:
            email_clean = email.strip()
            if email_clean and '@' in email_clean:
                recipients.add(email_clean)

    # 2. Selected distribution lists
    for lid in list_ids:
        if lid:
            resolved_emails = DistributionListService.resolve_recipients(int(lid))
            recipients.update(resolved_emails)

    if not recipients:
        return jsonify({'success': False, 'error': 'No valid recipient email addresses found.'})

    if not subject or not body:
        return jsonify({'success': False, 'error': 'Subject and Body are required.'})

    try:
        delivered = EmailService.send_raw_email_batch(
            recipients=list(recipients),
            subject=subject,
            body=body,
            user_id=session.get('user_id')
        )
        AuditLog.log_action(
            action='ADD',
            table_name='email_logs',
            record_id=0,
            description=f"Sent batch email broadcast '{subject}' to {len(recipients)} recipients ({delivered} delivered)"
        )
        db.session.commit()
        return jsonify({
            'success': True,
            'recipientsCount': len(recipients),
            'deliveredCount': delivered
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@email_hub_bp.route('/drafts/save', methods=['POST'])
@admin_or_employee_required
def save_draft():
    data = request.json or {}
    draft_id = data.get('draft_id')
    subject = data.get('subject')
    body = data.get('body')
    recipients_raw = data.get('recipients_raw')
    list_ids = data.get('distribution_lists', [])

    list_ids_str = ",".join(str(lid) for lid in list_ids) if list_ids else ""

    try:
        if draft_id:
            draft = EmailDraft.query.filter_by(draftID=draft_id, createdByUserID=session.get('user_id')).first()
            if not draft:
                return jsonify({'success': False, 'error': 'Draft not found.'})
            draft.subject = subject
            draft.body = body
            draft.recipientsRaw = recipients_raw
            draft.selectedDistributionListIDsRaw = list_ids_str
            draft.lastUpdated = datetime.utcnow()

            AuditLog.log_action(
                action='EDIT',
                table_name='email_drafts',
                record_id=draft_id,
                description=f"Updated email draft #{draft_id} '{subject or 'Untitled'}'"
            )
        else:
            draft = EmailDraft(
                subject=subject,
                body=body,
                recipientsRaw=recipients_raw,
                selectedDistributionListIDsRaw=list_ids_str,
                createdByUserID=session.get('user_id')
            )
            db.session.add(draft)
            db.session.flush()

            AuditLog.log_action(
                action='ADD',
                table_name='email_drafts',
                record_id=draft.draftID,
                description=f"Created email draft #{draft.draftID} '{subject or 'Untitled'}'"
            )
        
        db.session.commit()
        return jsonify({'success': True, 'draft_id': draft.draftID})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@email_hub_bp.route('/drafts/get/<int:id>')
@admin_or_employee_required
def get_draft(id):
    draft = EmailDraft.query.filter_by(draftID=id, createdByUserID=session.get('user_id')).first_or_404()
    lists = [int(x) for x in draft.selectedDistributionListIDsRaw.split(',') if x.strip()] if draft.selectedDistributionListIDsRaw else []
    return jsonify({
        'success': True,
        'draft_id': draft.draftID,
        'subject': draft.subject,
        'body': draft.body,
        'recipients_raw': draft.recipientsRaw,
        'distribution_lists': lists
    })

@email_hub_bp.route('/drafts/delete/<int:id>', methods=['POST'])
@admin_or_employee_required
def delete_draft(id):
    draft = EmailDraft.query.filter_by(draftID=id, createdByUserID=session.get('user_id')).first_or_404()
    try:
        AuditLog.log_action(
            action='DELETE',
            table_name='email_drafts',
            record_id=id,
            description=f"Deleted email draft #{id} '{draft.subject or 'Untitled'}'"
        )
        db.session.delete(draft)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@email_hub_bp.route('/logs/view/<int:id>')
@admin_or_employee_required
def view_log(id):
    log = EmailLog.query.get_or_404(id)
    role = session.get('role_name', '').lower()
    if role != 'admin' and log.createdByUserID != session.get('user_id'):
        return jsonify({'success': False, 'error': 'Access Denied: You can only view logs for emails you sent.'}), 403

    return jsonify({
        'success': True,
        'emailLogID': log.emailLogID,
        'recipients': log.recipientsRaw,
        'subject': log.subject,
        'body': log.body,
        'emailType': log.emailType,
        'status': log.status,
        'sentAt': log.sentAt.strftime('%Y-%m-%d %H:%M:%S') if log.sentAt else None,
        'attempts': log.attempts,
        'lastError': log.lastError,
        'templateKey': log.templateKey,
        'createdAt': log.createdAt.strftime('%Y-%m-%d %H:%M:%S')
    })

@email_hub_bp.route('/reminders/run-now', methods=['POST'])
@admin_required
def run_reminders_now():
    from app.services.reminder_service import ReminderService
    try:
        results = ReminderService.process_all_reminders()
        total_processed = sum(results.values())
        return jsonify({
            'success': True,
            'message': f"Automated background reminder cycle executed successfully ({total_processed} reminder tasks processed).",
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



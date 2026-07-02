import re
from app.models.base import db
from app.models.users import Users, Role, Blacklist
from app.models.email_hub import DistributionList, DistributionListMember, DistributionListRule

class DistributionListService:
    @staticmethod
    def resolve_recipients(distribution_list_id):
        """
        Resolves a list of recipient emails dynamically based on direct members
        and dynamic filtering rules for a given Distribution List ID.
        """
        dist_list = DistributionList.query.get(distribution_list_id)
        if not dist_list or not dist_list.isActive:
            return []

        recipients = set()

        # 1. Fetch direct active members
        direct_members = DistributionListMember.query.filter_by(
            distributionListID=distribution_list_id,
            isActive=True
        ).all()
        for member in direct_members:
            if member.email and member.email.strip():
                recipients.add(member.email.strip().lower())

        # 2. Process rules
        rules = DistributionListRule.query.filter_by(distributionListID=distribution_list_id).all()
        for rule in rules:
            # Query role names
            roles_to_include = []
            if rule.includeCustomers:
                roles_to_include.append('Customer')
            if rule.includeEmployees:
                roles_to_include.extend(['Employee', 'Accountant'])
            if rule.includeAdmins:
                roles_to_include.append('Admin')

            if roles_to_include:
                # Query users that have matching roles and statuses
                user_query = Users.query.join(Role).filter(Role.roleName.in_(roles_to_include))
                if rule.onlyActiveUsers:
                    user_query = user_query.filter(Users.status == 'Active')
                
                users = user_query.all()
                
                # Retrieve blacklisted user IDs to exclude if requested
                excluded_user_ids = set()
                if rule.excludeBlacklistedCustomers:
                    # Filter active blacklist entries
                    active_blacklisted = Blacklist.query.filter(
                        (Blacklist.status == 'Active') | (Blacklist.status.is_(None))
                    ).all()
                    for bl in active_blacklisted:
                        excluded_user_ids.add(bl.userID)

                for user in users:
                    if user.userID not in excluded_user_ids:
                        if user.email and user.email.strip():
                            recipients.add(user.email.strip().lower())

            # 3. Resolve manual raw emails (split by comma, semicolon, space, newline)
            if rule.manualEmailsRaw:
                manuals = re.split(r'[,\s;\n\r]+', rule.manualEmailsRaw)
                for email in manuals:
                    email_clean = email.strip().lower()
                    # Basic email format check
                    if email_clean and '@' in email_clean:
                        recipients.add(email_clean)

        return list(recipients)

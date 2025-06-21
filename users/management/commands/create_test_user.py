from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a test user with specified credentials and role if it does not exist.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='testuser', help='Username for the test user')
        parser.add_argument('--email', type=str, default='testuser@example.com', help='Email for the test user')
        parser.add_argument('--password', type=str, default='testpassword', help='Password for the test user')
        parser.add_argument('--role', type=str, default='user', help='Role for the test user')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        role = options['role']

        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, email=email, password=password, role=role)
            self.stdout.write(self.style.SUCCESS(f"Successfully created test user '{username}' with role '{role}'"))
        else:
            user = User.objects.get(username=username)
            if user.role != role:
                user.role = role
                user.save(update_fields=['role'])
                self.stdout.write(self.style.WARNING(f"User '{username}' already exists. Role updated to '{role}'."))
            else:
                self.stdout.write(self.style.WARNING(f"User '{username}' with role '{role}' already exists."))

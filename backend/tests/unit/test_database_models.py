# Unit tests for database models

import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.main_auth_async import (
    User,
    UserRole,
    LicenseType,
    Base,
    hash_password,
    verify_password
)


@pytest.mark.unit
@pytest.mark.database
class TestUserModel:
    """Test cases for User database model."""
    
    @pytest.mark.asyncio
    async def test_user_creation(self, async_db):
        """Test basic user creation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password123"),
            first_name="Test",
            last_name="User",
            role=UserRole.THERAPIST,
            license_type=LicenseType.LMFT,
            license_number="TEST123456",
            license_state="CA",
            is_active=True,
            is_verified=True
        )
        
        async_db.add(user)
        await async_db.commit()
        await async_db.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.role == UserRole.THERAPIST
        assert user.license_type == LicenseType.LMFT
        assert user.license_number == "TEST123456"
        assert user.license_state == "CA"
        assert user.is_active is True
        assert user.is_verified is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_user_email_uniqueness(self, async_db):
        """Test that email addresses must be unique."""
        user1 = User(
            email="duplicate@example.com",
            username="user1",
            hashed_password=hash_password("password123"),
            first_name="User",
            last_name="One",
            role=UserRole.THERAPIST
        )
        
        user2 = User(
            email="duplicate@example.com",
            username="user2",
            hashed_password=hash_password("password123"),
            first_name="User",
            last_name="Two",
            role=UserRole.THERAPIST
        )
        
        async_db.add(user1)
        await async_db.commit()
        
        async_db.add(user2)
        with pytest.raises(IntegrityError):
            await async_db.commit()
    
    @pytest.mark.asyncio
    async def test_user_username_uniqueness(self, async_db):
        """Test that usernames must be unique."""
        user1 = User(
            email="user1@example.com",
            username="duplicate",
            hashed_password=hash_password("password123"),
            first_name="User",
            last_name="One",
            role=UserRole.THERAPIST
        )
        
        user2 = User(
            email="user2@example.com",
            username="duplicate",
            hashed_password=hash_password("password123"),
            first_name="User",
            last_name="Two",
            role=UserRole.THERAPIST
        )
        
        async_db.add(user1)
        await async_db.commit()
        
        async_db.add(user2)
        with pytest.raises(IntegrityError):
            await async_db.commit()
    
    @pytest.mark.asyncio
    async def test_user_required_fields(self, async_db):
        """Test that required fields are enforced."""
        # Missing email
        with pytest.raises(IntegrityError):
            user = User(
                username="testuser",
                hashed_password=hash_password("password123"),
                first_name="Test",
                last_name="User",
                role=UserRole.THERAPIST
            )
            async_db.add(user)
            await async_db.commit()
        
        await async_db.rollback()
        
        # Missing username
        with pytest.raises(IntegrityError):
            user = User(
                email="test@example.com",
                hashed_password=hash_password("password123"),
                first_name="Test",
                last_name="User",
                role=UserRole.THERAPIST
            )
            async_db.add(user)
            await async_db.commit()
        
        await async_db.rollback()
        
        # Missing password
        with pytest.raises(IntegrityError):
            user = User(
                email="test@example.com",
                username="testuser",
                first_name="Test",
                last_name="User",
                role=UserRole.THERAPIST
            )
            async_db.add(user)
            await async_db.commit()
    
    @pytest.mark.asyncio
    async def test_user_defaults(self, async_db):
        """Test user model default values."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password123"),
            first_name="Test",
            last_name="User"
        )
        
        async_db.add(user)
        await async_db.commit()
        await async_db.refresh(user)
        
        assert user.role == UserRole.STUDENT  # Default role
        assert user.license_type == LicenseType.STUDENT  # Default license
        assert user.is_active is True
        assert user.is_verified is False
        assert user.license_number is None
        assert user.license_state is None
    
    @pytest.mark.asyncio
    async def test_user_password_hashing(self, async_db):
        """Test that passwords are properly hashed."""
        plain_password = "mypassword123"
        hashed_password = hash_password(plain_password)
        
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            first_name="Test",
            last_name="User",
            role=UserRole.THERAPIST
        )
        
        async_db.add(user)
        await async_db.commit()
        await async_db.refresh(user)
        
        # Password should be hashed (not plain text)
        assert user.hashed_password != plain_password
        assert len(user.hashed_password) > 0
        
        # Should be able to verify password
        assert verify_password(plain_password, user.hashed_password)
        assert not verify_password("wrongpassword", user.hashed_password)
    
    @pytest.mark.asyncio
    async def test_user_timestamps(self, async_db):
        """Test that timestamps are automatically set."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password123"),
            first_name="Test",
            last_name="User",
            role=UserRole.THERAPIST
        )
        
        async_db.add(user)
        await async_db.commit()
        await async_db.refresh(user)
        
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        
        # Timestamps should be in UTC
        assert user.created_at.tzinfo == timezone.utc
        assert user.updated_at.tzinfo == timezone.utc
    
    @pytest.mark.asyncio
    async def test_user_update_timestamp(self, async_db):
        """Test that updated_at is changed when user is modified."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password123"),
            first_name="Test",
            last_name="User",
            role=UserRole.THERAPIST
        )
        
        async_db.add(user)
        await async_db.commit()
        await async_db.refresh(user)
        
        original_updated_at = user.updated_at
        
        # Update user
        user.first_name = "Updated"
        await async_db.commit()
        await async_db.refresh(user)
        
        assert user.updated_at > original_updated_at
    
    @pytest.mark.asyncio
    async def test_user_is_licensed_property(self, async_db):
        """Test the is_licensed property."""
        # Licensed therapist
        therapist = User(
            email="therapist@example.com",
            username="therapist",
            hashed_password=hash_password("password123"),
            first_name="Licensed",
            last_name="Therapist",
            role=UserRole.THERAPIST,
            license_type=LicenseType.LMFT,
            license_number="LIC123456",
            license_state="CA"
        )
        
        async_db.add(therapist)
        await async_db.commit()
        await async_db.refresh(therapist)
        
        assert therapist.is_licensed is True
        
        # Student user
        student = User(
            email="student@example.com",
            username="student",
            hashed_password=hash_password("password123"),
            first_name="Student",
            last_name="User",
            role=UserRole.STUDENT,
            license_type=LicenseType.STUDENT
        )
        
        async_db.add(student)
        await async_db.commit()
        await async_db.refresh(student)
        
        assert student.is_licensed is False
    
    @pytest.mark.asyncio
    async def test_user_full_name_property(self, async_db):
        """Test the full_name property."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password123"),
            first_name="John",
            last_name="Doe",
            role=UserRole.THERAPIST
        )
        
        async_db.add(user)
        await async_db.commit()
        await async_db.refresh(user)
        
        assert user.full_name == "John Doe"
    
    @pytest.mark.asyncio
    async def test_user_string_representation(self, async_db):
        """Test user string representation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password123"),
            first_name="Test",
            last_name="User",
            role=UserRole.THERAPIST
        )
        
        async_db.add(user)
        await async_db.commit()
        await async_db.refresh(user)
        
        assert str(user) == "testuser (test@example.com)"
    
    @pytest.mark.asyncio
    async def test_user_query_by_email(self, async_db):
        """Test querying users by email."""
        user = User(
            email="query@example.com",
            username="queryuser",
            hashed_password=hash_password("password123"),
            first_name="Query",
            last_name="User",
            role=UserRole.THERAPIST
        )
        
        async_db.add(user)
        await async_db.commit()
        
        # Query by email
        result = await async_db.execute(
            select(User).where(User.email == "query@example.com")
        )
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.email == "query@example.com"
        assert found_user.username == "queryuser"
    
    @pytest.mark.asyncio
    async def test_user_query_by_username(self, async_db):
        """Test querying users by username."""
        user = User(
            email="query@example.com",
            username="queryuser",
            hashed_password=hash_password("password123"),
            first_name="Query",
            last_name="User",
            role=UserRole.THERAPIST
        )
        
        async_db.add(user)
        await async_db.commit()
        
        # Query by username
        result = await async_db.execute(
            select(User).where(User.username == "queryuser")
        )
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.username == "queryuser"
        assert found_user.email == "query@example.com"
    
    @pytest.mark.asyncio
    async def test_user_active_filter(self, async_db):
        """Test filtering users by active status."""
        active_user = User(
            email="active@example.com",
            username="activeuser",
            hashed_password=hash_password("password123"),
            first_name="Active",
            last_name="User",
            role=UserRole.THERAPIST,
            is_active=True
        )
        
        inactive_user = User(
            email="inactive@example.com",
            username="inactiveuser",
            hashed_password=hash_password("password123"),
            first_name="Inactive",
            last_name="User",
            role=UserRole.THERAPIST,
            is_active=False
        )
        
        async_db.add(active_user)
        async_db.add(inactive_user)
        await async_db.commit()
        
        # Query only active users
        result = await async_db.execute(
            select(User).where(User.is_active == True)
        )
        active_users = result.scalars().all()
        
        assert len(active_users) == 1
        assert active_users[0].username == "activeuser"
    
    @pytest.mark.asyncio
    async def test_user_role_filter(self, async_db):
        """Test filtering users by role."""
        therapist = User(
            email="therapist@example.com",
            username="therapist",
            hashed_password=hash_password("password123"),
            first_name="Therapist",
            last_name="User",
            role=UserRole.THERAPIST
        )
        
        student = User(
            email="student@example.com",
            username="student",
            hashed_password=hash_password("password123"),
            first_name="Student",
            last_name="User",
            role=UserRole.STUDENT
        )
        
        admin = User(
            email="admin@example.com",
            username="admin",
            hashed_password=hash_password("password123"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN
        )
        
        async_db.add(therapist)
        async_db.add(student)
        async_db.add(admin)
        await async_db.commit()
        
        # Query therapists only
        result = await async_db.execute(
            select(User).where(User.role == UserRole.THERAPIST)
        )
        therapists = result.scalars().all()
        
        assert len(therapists) == 1
        assert therapists[0].username == "therapist"
        
        # Query students only
        result = await async_db.execute(
            select(User).where(User.role == UserRole.STUDENT)
        )
        students = result.scalars().all()
        
        assert len(students) == 1
        assert students[0].username == "student"


@pytest.mark.unit
@pytest.mark.database
class TestUserRoleEnum:
    """Test cases for UserRole enum."""
    
    def test_user_role_values(self):
        """Test UserRole enum values."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.THERAPIST.value == "therapist"
        assert UserRole.STUDENT.value == "student"
    
    def test_user_role_enum_membership(self):
        """Test UserRole enum membership."""
        assert "admin" in [role.value for role in UserRole]
        assert "therapist" in [role.value for role in UserRole]
        assert "student" in [role.value for role in UserRole]
        assert "invalid_role" not in [role.value for role in UserRole]


@pytest.mark.unit
@pytest.mark.database
class TestLicenseTypeEnum:
    """Test cases for LicenseType enum."""
    
    def test_license_type_values(self):
        """Test LicenseType enum values."""
        assert LicenseType.LMFT.value == "LMFT"
        assert LicenseType.LCSW.value == "LCSW"
        assert LicenseType.LPC.value == "LPC"
        assert LicenseType.STUDENT.value == "STUDENT"
    
    def test_license_type_enum_membership(self):
        """Test LicenseType enum membership."""
        assert "LMFT" in [license.value for license in LicenseType]
        assert "LCSW" in [license.value for license in LicenseType]
        assert "LPC" in [license.value for license in LicenseType]
        assert "STUDENT" in [license.value for license in LicenseType]
        assert "INVALID_LICENSE" not in [license.value for license in LicenseType]


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseBase:
    """Test cases for database base class."""
    
    def test_base_metadata(self):
        """Test that Base has proper metadata."""
        assert hasattr(Base, 'metadata')
        assert Base.metadata is not None
    
    def test_user_table_exists(self):
        """Test that User table is registered with Base."""
        table_names = [table.name for table in Base.metadata.tables.values()]
        assert "users" in table_names
    
    def test_user_table_columns(self):
        """Test User table column definitions."""
        user_table = Base.metadata.tables["users"]
        column_names = [column.name for column in user_table.columns]
        
        # Required columns
        assert "id" in column_names
        assert "email" in column_names
        assert "username" in column_names
        assert "hashed_password" in column_names
        assert "first_name" in column_names
        assert "last_name" in column_names
        assert "role" in column_names
        assert "license_type" in column_names
        assert "is_active" in column_names
        assert "is_verified" in column_names
        assert "created_at" in column_names
        assert "updated_at" in column_names
        
        # Optional columns
        assert "license_number" in column_names
        assert "license_state" in column_names
    
    def test_user_table_constraints(self):
        """Test User table constraints."""
        user_table = Base.metadata.tables["users"]
        
        # Check unique constraints
        unique_constraints = [constraint.name for constraint in user_table.constraints 
                            if hasattr(constraint, 'columns')]
        
        # Primary key should exist
        assert user_table.primary_key is not None
        
        # Check for email and username uniqueness (implementation may vary)
        email_column = user_table.columns["email"]
        username_column = user_table.columns["username"]
        
        assert email_column.unique is True or any(constraint.columns == {email_column} 
                                                for constraint in user_table.constraints)
        assert username_column.unique is True or any(constraint.columns == {username_column} 
                                                   for constraint in user_table.constraints)
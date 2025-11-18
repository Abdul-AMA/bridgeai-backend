import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.invitation import Invitation
from app.core.config import settings


def generate_invitation_token() -> str:
    """Generate a unique invitation token using UUID4."""
    return uuid.uuid4().hex


def create_invitation(
    db: Session,
    team_id: int,
    email: str,
    role: str,
    invited_by_user_id: int,
    expires_in_days: int = 7
) -> Invitation:
    """
    Create a new team invitation.
    
    Args:
        db: Database session
        team_id: ID of the team
        email: Email of the invitee
        role: Role to assign (owner, admin, member, viewer)
        invited_by_user_id: ID of the user sending the invitation
        expires_in_days: Number of days until invitation expires
    
    Returns:
        Created Invitation object
    """
    token = generate_invitation_token()
    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    invitation = Invitation(
        email=email,
        role=role,
        team_id=team_id,
        invited_by_user_id=invited_by_user_id,
        token=token,
        status='pending',
        expires_at=expires_at
    )
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    return invitation


def send_invitation_email_to_console(email: str, invite_link: str, team_name: str = None):
    """
    Send invitation email (console version for development).
    
    In production, this would send a real email via SMTP.
    For now, it prints to the console.
    
    Args:
        email: Recipient email address
        invite_link: Full invitation acceptance link
        team_name: Name of the team (optional)
    """
    print("\n" + "="*80)
    print("📧 INVITATION EMAIL (Console)")
    print("="*80)
    print(f"To: {email}")
    if team_name:
        print(f"Subject: You've been invited to join {team_name} on BridgeAI")
    else:
        print(f"Subject: You've been invited to join a team on BridgeAI")
    print("-"*80)
    print(f"\nYou've been invited to join a team!")
    print(f"\nClick the link below to accept the invitation:")
    print(f"\n{invite_link}")
    print(f"\nThis invitation will expire in 7 days.")
    print("="*80 + "\n")


def build_invitation_link(token: str) -> str:
    """
    Build the full invitation acceptance link.
    
    Args:
        token: Invitation token
    
    Returns:
        Full URL for accepting invitation
    """
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    return f"{frontend_url}/invite/accept?token={token}"

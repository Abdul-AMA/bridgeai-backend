# Team Invitations Feature - Testing Guide

## ✅ Implementation Complete!

The team invitation system with console-based emails has been successfully implemented.

---

## 📋 **What Was Created:**

### **1. Database Model** (`app/models/invitation.py`)
- `Invitation` table with all required fields
- `InvitationStatus` enum: pending, accepted, expired, canceled
- Expiration checking methods
- Relationships to Team and User models

### **2. Schemas** (`app/schemas/invitation.py`)
- `InvitationCreate` - for creating invitations (email + role validation)
- `InvitationOut` - full invitation details
- `InvitationPublicOut` - public view (without token)
- `InvitationResponse` - response with invite link
- `InvitationAcceptResponse` - acceptance confirmation

### **3. Utilities** (`app/utils/invitation.py`)
- `generate_invitation_token()` - UUID4 token generator
- `create_invitation()` - creates invitation with 7-day expiration
- `send_invitation_email_to_console()` - prints invitation to console
- `build_invitation_link()` - constructs frontend URL

### **4. API Endpoints**

#### **Team Invitations:**
- `POST /api/teams/{team_id}/invite` - Send invitation (owners/admins only)

#### **Invitation Management:**
- `GET /invitation/{token}` - View invitation details (public)
- `POST /invitation/{token}/accept` - Accept invitation (authenticated)

### **5. Database Migration**
- Migration `237afc01f63d_add_invitations_table.py` applied successfully
- `invitations` table created with all constraints

---

## 🧪 **How to Test:**

### **Step 1: Create a Team**
```http
POST /api/teams/
Authorization: Bearer {ba_token}

{
  "name": "Development Team",
  "description": "Main dev team"
}
```

### **Step 2: Send Invitation**
```http
POST /api/teams/1/invite
Authorization: Bearer {ba_token}

{
  "email": "newmember@example.com",
  "role": "member"
}
```

**Console Output:**
```
================================================================================
📧 INVITATION EMAIL (Console)
================================================================================
To: newmember@example.com
Subject: You've been invited to join Development Team on BridgeAI
--------------------------------------------------------------------------------

You've been invited to join a team!

Click the link below to accept the invitation:

http://localhost:3000/invite/accept?token=a1b2c3d4e5f6...

This invitation will expire in 7 days.
================================================================================
```

**Response:**
```json
{
  "invite_link": "http://localhost:3000/invite/accept?token=a1b2c3d4e5f6...",
  "status": "pending",
  "invitation": {
    "id": 1,
    "email": "newmember@example.com",
    "role": "member",
    "team_id": 1,
    "invited_by_user_id": 1,
    "token": "a1b2c3d4e5f6...",
    "status": "pending",
    "created_at": "2025-11-17T12:00:00",
    "expires_at": "2025-11-24T12:00:00"
  }
}
```

### **Step 3: View Invitation (Public)**
```http
GET /invitation/{token}
```

**Response:**
```json
{
  "email": "newmember@example.com",
  "role": "member",
  "team_id": 1,
  "status": "pending",
  "created_at": "2025-11-17T12:00:00",
  "expires_at": "2025-11-24T12:00:00"
}
```

### **Step 4: Accept Invitation**
```http
POST /invitation/{token}/accept
Authorization: Bearer {user_token}
```

**Response:**
```json
{
  "message": "Invitation accepted successfully",
  "team_id": 1,
  "role": "member"
}
```

---

## 🔐 **Security Features:**

✅ Only owners and admins can send invitations  
✅ Tokens are UUID4 (secure and unique)  
✅ Invitations expire after 7 days  
✅ Email must match authenticated user  
✅ Prevents duplicate pending invitations  
✅ Checks for existing team membership  
✅ Expired invitations automatically marked  

---

## 📊 **Database Schema:**

```sql
CREATE TABLE invitations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(256) NOT NULL,
    role VARCHAR(50) NOT NULL,
    team_id INT NOT NULL,
    invited_by_user_id INT NOT NULL,
    token VARCHAR(64) NOT NULL UNIQUE,
    status ENUM('pending', 'accepted', 'expired', 'canceled') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (invited_by_user_id) REFERENCES users(id),
    
    INDEX idx_email (email),
    INDEX idx_token (token)
);
```

---

## 🎯 **Business Rules:**

1. **Who can invite?** Owners and admins only
2. **Who can accept?** Any authenticated user with matching email
3. **Expiration:** 7 days from creation
4. **Duplicate checks:** No pending invitations to same email
5. **Already members:** Can't accept if already in team
6. **Email matching:** Must match invited email exactly

---

## 🚀 **Ready to Use!**

All endpoints are live and ready for testing. The console will show invitation "emails" for development/testing purposes.

In production, replace `send_invitation_email_to_console()` with actual SMTP email sending.

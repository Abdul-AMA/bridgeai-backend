# Team Invitations - Frontend Task

## Task Overview
Implement the team invitation feature that allows team owners/admins to invite users by email and enables invited users to accept invitations to join teams.

---

## Backend API Endpoints (Ready to Use)

**Base URL:** `http://127.0.0.1:8000`

### 1. Send Team Invitation
```
POST /api/teams/{team_id}/invite
```
**Auth:** Required (Owner/Admin only)  
**Body:**
```json
{
  "email": "user@example.com",
  "role": "member"
}
```
**Roles:** `owner`, `admin`, `member`, `viewer`

**Success Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "role": "member",
  "team_id": "123e4567-e89b-12d3-a456-426614174000",
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "status": "pending",
  "created_at": "2025-11-17T10:30:00",
  "expires_at": "2025-11-24T10:30:00"
}
```

**Errors:**
- `403` - Not owner/admin
- `409` - User already member or invited
- `400` - Invalid email/role

---

### 2. View Invitation Details
```
GET /api/invitation/{token}
```
**Auth:** Not required (public)

**Success Response (200):**
```json
{
  "email": "user@example.com",
  "role": "member",
  "team_name": "Development Team",
  "invited_by": "John Doe",
  "created_at": "2025-11-17T10:30:00",
  "expires_at": "2025-11-24T10:30:00",
  "status": "pending"
}
```

**Errors:**
- `404` - Invalid token
- `400` - Invitation expired

---

### 3. Accept Invitation
```
POST /api/invitation/{token}/accept
```
**Auth:** Required  
**Body:** Empty

**Success Response (200):**
```json
{
  "message": "Successfully joined the team",
  "team": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Development Team",
    "description": "Our main development team"
  },
  "role": "member"
}
```

**Errors:**
- `400` - Expired or email mismatch
- `401` - Not logged in
- `404` - Invalid token
- `409` - Already a member

---

### 4. List Team Invitations
```
GET /api/teams/{team_id}/invitations
```
**Auth:** Required (Owner/Admin only)  
**Query Params:** `include_expired` (boolean, default: false)

**Success Response (200):**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "role": "member",
    "team_id": 3,
    "invited_by_user_id": 5,
    "token": "a1b2c3d4...",
    "status": "pending",
    "created_at": "2025-11-17T10:30:00",
    "expires_at": "2025-11-24T10:30:00"
  }
]
```

**Errors:**
- `403` - Not owner/admin
- `404` - Team not found

---

### 5. Get Team Members (with User Info)
```
GET /api/teams/{team_id}/members
```
**Auth:** Required (Team member)  
**Query Params:** `include_inactive` (boolean, default: false)

**Success Response (200):**
```json
[
  {
    "id": 1,
    "team_id": 3,
    "user_id": 5,
    "role": "owner",
    "is_active": true,
    "joined_at": "2025-11-01T10:00:00",
    "updated_at": "2025-11-01T10:00:00",
    "user": {
      "id": 5,
      "full_name": "John Doe",
      "email": "john@example.com",
      "role": "ba"
    }
  }
]
```

**Note:** User details are now included automatically - no need for separate API calls!

**Errors:**
- `403` - Not a team member
- `404` - Team not found

---

### 6. Get User by ID
```
GET /api/auth/users/{user_id}
```
**Auth:** Required

**Success Response (200):**
```json
{
  "id": 5,
  "full_name": "John Doe",
  "email": "john@example.com",
  "role": "ba",
  "created_at": "2025-10-01T10:00:00"
}
```

**Errors:**
- `401` - Not authenticated
- `404` - User not found

---

### 7. Get Current User
```
GET /api/auth/me
```
**Auth:** Required

**Success Response (200):**
```json
{
  "id": 5,
  "full_name": "John Doe",
  "email": "john@example.com",
  "role": "ba",
  "created_at": "2025-10-01T10:00:00"
}
```

---

## Implementation Requirements

### Part 1: Invite Member UI (Team Page)

**Where:** Team members/settings page

**Requirements:**
1. Add "Invite Member" button (visible only to owners/admins)
2. Create invitation modal/form with:
   - Email input (validated)
   - Role dropdown (owner/admin/member/viewer)
3. On submit:
   - Call `POST /api/teams/{team_id}/invite`
   - Show success: "Invitation sent to {email}"
   - Close modal

**Code Example:**
```typescript
async function sendInvitation(teamId: string, email: string, role: string) {
  const response = await fetch(`http://127.0.0.1:8000/api/teams/${teamId}/invite`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({ email, role })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}
```

---

### Part 2: Accept Invitation Page

**Route:** `/invite/accept?token={token}`

**Requirements:**
1. On page load:
   - Extract token from URL query params
   - Call `GET /api/invitation/{token}` to fetch details
   - Display: team name, role, invited by, expiration

2. If user not logged in:
   - Show login prompt with return URL
   - After login, redirect back to invitation page

3. If logged in:
   - Check if email matches (show warning if not)
   - Show "Accept Invitation" button
   - On click: Call `POST /api/invitation/{token}/accept`
   - On success: Redirect to `/teams/{team_id}`

**Code Example:**
```typescript
// Fetch invitation details
async function getInvitationDetails(token: string) {
  const response = await fetch(`http://127.0.0.1:8000/api/invitation/${token}`);
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Invitation not found or has expired');
    }
    throw new Error('Failed to load invitation');
  }
  
  return await response.json();
}

// Accept invitation
async function acceptInvitation(token: string, accessToken: string) {
  const response = await fetch(`http://127.0.0.1:8000/api/invitation/${token}/accept`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}
```

---

## TypeScript Types

```typescript
interface InvitationRequest {
  email: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
}

interface InvitationDetails {
  email: string;
  role: string;
  team_name: string;
  invited_by: string;
  created_at: string;
  expires_at: string;
  status: string;
}

interface InvitationAcceptResponse {
  message: string;
  team: {
    id: string;
    name: string;
    description: string;
  };
  role: string;
}
```

---

## User Flow

### Inviting a Member
1. Team owner/admin goes to team page
2. Clicks "Invite Member"
3. Enters email and selects role
4. Submits form
5. Backend sends email (currently prints to console)
6. Invited user receives link: `http://localhost:3000/invite/accept?token=abc123...`

### Accepting Invitation
1. User clicks invitation link from email
2. Page loads and fetches invitation details
3. If not logged in → login page → return to invitation
4. If logged in → shows team details and "Accept" button
5. User clicks "Accept"
6. Added to team and redirected to team page

---

## Testing

### Test Scenario 1: Send Invitation
1. Login as team owner
2. Go to team page
3. Click "Invite Member"
4. Enter valid email and role
5. Submit
6. ✅ Should see success message
7. ✅ Check backend console for invitation link

### Test Scenario 2: Accept Invitation
1. Copy invitation link from backend console
2. Open link in browser
3. ✅ Should see team details
4. Login if needed
5. Click "Accept"
6. ✅ Should redirect to team page
7. ✅ Should see yourself in team members list

### Test Scenario 3: Email Mismatch
1. Get invitation link for `user1@example.com`
2. Login as `user2@example.com`
3. Try to accept
4. ✅ Should show error about email mismatch

### Test Scenario 4: Expired/Invalid Token
1. Use invalid token in URL
2. ✅ Should show "Invitation not found" error

---

## Important Notes

1. **Email Console:** During development, invitation emails print to the backend terminal (check console for links)

2. **7-Day Expiration:** Invitations expire after 7 days automatically

3. **Email Validation:** The logged-in user's email must match the invitation email

4. **Single-Use Tokens:** Each token can only be used once

5. **Authentication:** Accept endpoint requires user to be logged in

---

## Environment Setup

Add to `.env`:
```
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_FRONTEND_URL=http://localhost:3000
```

---

## Backend Status

✅ All endpoints implemented and tested  
✅ Database migrations applied  
✅ Server running on `http://127.0.0.1:8000`  
✅ Console-based email system active  
✅ 7-day expiration working  
✅ Role-based permissions enforced  

**API Documentation:** http://127.0.0.1:8000/docs

---

## Need Help?

- Check backend console for invitation links (emails print there)
- Use http://127.0.0.1:8000/docs for interactive API testing
- Check `INVITATIONS_GUIDE.md` for backend testing examples

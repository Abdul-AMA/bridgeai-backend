Here’s a **focused, integrated update** of your BRD with the Reconciliation feature embedded properly into the system (not as a separate add-on).

---

# **Business Requirements Document (BRD): Halaqa Management System (Updated)**

## **1. Executive Summary & Objective**

The Halaqa Management System digitizes and streamlines Quranic learning operations, with strong emphasis on:

* Daily tracking of student attendance and achievements
* Structured weekly planning
* Automated progress measurement
* **Data reconciliation to ensure integrity between plans, attendance, and achievements**

---

## **2. Technical Architecture & Constraints**

### **Core Stack**

* Database: MySQL
* Backend: NestJS
* Frontend: Nuxt.js (Nuxt UI)

### **Database Rules**

* Every entity must include:

  * `id`
  * `created_at`
  * `updated_at`
  * `deleted_at` (soft delete)

### **Integrity Principle (NEW)**

All core transactional data must be **reconcilable**, meaning:

* No achievement exists without valid attendance context
* No plan exists without measurable progress linkage
* All records must support traceability across:

  * Student
  * Halaqa
  * Teacher
  * Week scope

---

## **3. Core System Entities & Data Model (Updated)**

### **3.1 Quranic School**

Root entity for multi-tenancy (future-ready).

---

### **3.2 Admin**

Manages:

* Schools
* Teachers
* Halaqas

---

### **3.3 Teacher**

* Belongs to one School
* Manages multiple Halaqas

---

### **3.4 Halaqa**

* Managed by one Teacher
* Default logic: Memorization
* Contains:

  * Grading weights
  * **Reconciliation behavior settings (NEW)**:

    * Require achievement on attendance (boolean)
    * Allow unplanned achievements (boolean)

---

### **3.5 Student**

* Enrolled in multiple Halaqas (only one memorization)
* Stores capacity metrics
* Linked to parents

---

### **3.6 Parent**

* Can track multiple students

---

### **3.7 WeeklyPlan (Enhanced)**

Represents planned targets.

**New Fields:**

* `status` → (`due`, `completed`, `partial`, `overdue`, `excused`)
* `achieved_verses` (aggregated)
* `linked_achievements` (JSON)
* `is_status_manual_overridden` (boolean)
* `override_reason` (optional)

---

### **3.8 DailyAchievement**

Represents actual student work.

**New Flags:**

* `is_unplanned` (boolean)
* `is_flagged_conflict` (boolean)

---

### **3.9 Attendance**

Tracks:

* Present
* Late
* Excused

---

## **4. Functional Requirements**

---

## **4.1 Halaqa Setup & Attendance**

(Unchanged)

---

## **4.2 Achievement & Evaluation**

(Unchanged core, but now feeds reconciliation engine)

---

## **4.3 Weekly Planning**

(Unchanged core, with added reconciliation linkage)

---

# **4.4 Reconciliation Engine (NEW CORE MODULE)**

## **4.4.1 Overview**

A system-level engine that ensures **consistency between:**

* WeeklyPlan (expected)
* DailyAchievement (actual)
* Attendance (context)

Runs:

* On achievement submission (real-time)
* Via scheduled jobs (daily)

---

## **4.4.2 Objectives**

* Auto-calculate student progress
* Detect inconsistencies
* Maintain data integrity
* Provide actionable insights

---

## **4.4.3 Data Validation Rules**

### **Attendance ↔ Achievement**

* Flag:

  * Achievement exists + student absent
  * Student present + no achievement (if required)

### **Date Integrity**

* All matching occurs within:

  * `weekStartDate`
  * Halaqa schedule days

---

## **4.4.4 Status Calculation Logic**

Each `WeeklyPlan` entry must resolve to:

* **Completed**

  * Full or exceeded target achieved

* **Partial**

  * Partial verse coverage

* **Overdue**

  * Date passed, no achievement

* **Due**

  * Pending future or today

* **Excused**

  * Valid absence (e.g., approved excuse / holiday)

---

## **4.4.5 Matching Algorithm**

### **1. Range Matching**

* Match by:

  * Surah
  * Ayah range overlap

---

### **2. Partial Coverage**

* If achieved range ⊂ planned range → `partial`

---

### **3. Multi-Achievement Merge**

* Multiple achievements combined:

  * If total coverage ≥ plan → `completed`

---

### **4. Unplanned Detection**

* Achievement outside any plan:

  * Mark as `is_unplanned = true`
  * Flag for review

---

### **5. Linking**

* Store contributing achievements in:

  * `linked_achievements` (JSON)

---

## **4.4.6 Administrative Controls**

### **Manual Override**

* Lock status:

  * `is_status_manual_overridden = true`
* Disable automation for that record

---

### **Bulk Reconciliation**

* Scope:

  * Student
  * Halaqa
  * Week

---

## **4.4.7 Edge Case Handling**

* **Public Holidays**

  * Auto mark as `excused` or shift plan

* **Excused Absence**

  * Prevent `overdue`

* **Teacher Mismatch**

  * Log discrepancy without blocking reconciliation

---

## **4.4.8 Background Jobs**

* Daily cron:

  * Mark overdue plans
  * Detect missing achievements
  * Generate reconciliation flags

---

## **4.5 Reporting & Analytics (Enhanced)**

### **New Report Types**

#### **1. Reconciliation Report**

* Students with:

  * Missing achievements
  * Invalid attendance-achievement pairs
  * Unplanned achievements

---

#### **2. Plan Adherence Report**

* Completion rate
* Partial rate
* Overdue rate

---

#### **3. Teacher Compliance Report**

* Missing attendance entries
* Missing achievement logs
* Late data entry patterns

---

#### **4. Student Progress Visualization**

* Color-coded:

  * Green → Completed
  * Yellow → Partial
  * Red → Overdue
  * Blue → Due

---

## **5. Frontend Requirements (Nuxt UI)**

### **UI Components**

* Status badges (color-coded)
* Reconciliation dashboard:

  * Conflict list
  * Quick fix actions
* Plan vs Achievement timeline view

---

## **6. Backend Requirements (NestJS)**

### **Core Module**

* `ReconciliationService`

### **Responsibilities**

* Matching logic
* Status calculation
* Conflict detection
* Aggregation

---

### **Performance Requirements**

* Indexed fields:

  * `student_id`
  * `date`
  * `track_type`

---

## **7. Success Metrics**

* 100% plan-to-achievement traceability
* Zero orphaned achievements
* Automated status accuracy ≥ 99%
* Reduced manual tracking effort

---

## **What changed (short)**

* Reconciliation is now **core system logic**, not feature
* WeeklyPlan upgraded to a **state machine**
* Strong **data integrity rules** added
* System now **auditable + self-correcting**

---

If you want next step, I’d go one of these:

A) DB schema (tables + indexes + relations)
B) ReconciliationService design (methods + flow)
C) Event-driven architecture (cleanest for NestJS)

Pick one.

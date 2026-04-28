# Inventory System - Technical Debt & Improvement Roadmap

## 1. Code Architecture & Organization

### Missing Core Components
- [x] No Pydantic schemas for request/response validation in `schemas/`
- [x] Missing domain services - business logic is scattered in routers
- [x] No repository pattern - direct SQL queries in controllers
- [x] Incomplete error handling - minimal validation and error responses

## 2. Database Layer Issues

### Current Problems
- [x] Mixed connection handling - both `db/pool.py` and `db/connection.py` exist
- [x] No transaction management for complex operations
- [x] SQL injection risk - while parameterized, could be improved with query builder

## 3. Security & Authentication

### Current Issues
- [ ] Hardcoded credentials in `.env` file
- [x] Missing input validation - direct dict usage in `app/routers/items.py`
- [x] CORS for internal network only

## 4. Configuration Management

### Issues
- [ ] Sensitive data in version control - `.env` should be `.env.example`
- [x] Missing environment-specific configs
- [ ] No secrets management

## 5. Error Handling & Logging

### Missing
- [x] ~~Structured logging configuration~~
- [ ] Global exception handlers
- [x] ~~Request/response logging~~
- [x] ~~Health check improvements~~

## 6. Testing Infrastructure

### Completely Missing
- [ ] Integration tests
- [ ] Test database setup
- [x] ~~API endpoint tests~~

## 7. API Documentation & Validation

*To be documented*

## 8. Deployment & Operations

### Missing
- [x] ~~Environment health checks~~
- [ ] Monitoring endpoints

## 9. Database Schema Issues

### Problems in `inventory_ddl.sql`
- [x] Missing indexes for common queries
- [x] ~~No data validation constraints~~
- [x] Missing audit timestamps on some tables

## 10. Priority Implementation Order

### Immediate (Week 1)
- [x] ~~Add Pydantic schemas for request/response validation~~
- [x] ~~Fix security issues (remove `.env` from git, proper CORS)~~
- [x] ~~Add basic error handling~~

### Short-term (Week 2-3)
- [x] ~~Implement repository pattern~~
- [x] ~~Add domain services~~
- [ ] Set up proper testing framework

### Medium-term (Month 1)
- [x] ~~Add comprehensive logging~~
- [x] Implement database migrations
- [x] ~~Add monitoring and health checks~~

### Long-term (Month 2+)
- [x] Implement audit logging
- [ ] Add backup automation

---
# Frontend Refactoring Checklist: Bootstrap → Tailwind CSS

## Phase 0: Setup (Complete First)
- [x] `npm install -D tailwindcss postcss autoprefixer`
- [x] `npm install lucide-react`
- [x] `npx @tailwindcss/cli init -p`, using tailwind version 4.1.18
- [x] Update `src/index.css` with Tailwind directives
- [x] Update `src/main.tsx` (remove Bootstrap CSS, add index.css)

## Phase 1: Shared UI Components (Week 1)
- [x] Create `src/components/UI/` folder
- [x] Create `Button.tsx`
- [x] Create `Card.tsx` + exports
- [x] Create `Badge.tsx`
- [x] Create `Alert.tsx`
- [x] Create `Modal.tsx`
- [x] Create `Spinner.tsx`
- [x] Create `index.ts` barrel export
- [x] Create `Pagination.tsx`
- [x] Create `Form.tsx` components
- [x] Create icon mapping for `lucide-react`
- [ ] Test all components in Storybook (optional)

## Phase 2: Simple List Pages (Week 2)
- [x] `CategoryPage.tsx` ⭐ START HERE (simplest)
- [x] `UnitPage.tsx`
- [x] `UsersPage.tsx`
- [x] `ItemsPage.tsx`
- [x] `Dashboard.tsx`
- [x] Test search, filter, pagination on each

## Phase 3: Layout & Navigation (Week 2)
- [x] `Layout.tsx` (sidebar + responsive)
- [x] Remove `Layout.css` (move to Tailwind)
- [ ] Test desktop & mobile navigation
- [ ] Verify sub-menu collapse/expand

## Phase 4: Form Pages (Week 3)
- [x] `CategoryPage.tsx` modal (if not done in Phase 2)
- [x] `UnitPage.tsx` modal (if not done in Phase 2)
- [x] `ItemFormPage.tsx`
- [x] `IssueFormPage.tsx`
- [x] `UserFormPage.tsx`
- [x] `SettingsPage.tsx`

## Phase 5: Complex Pages (Week 3)
- [x] `Dashboard.tsx` (statistics + table)
- [x] `IssueDetailsPage.tsx`
- [x] `TransactionsPage.tsx`
- [x] `TransactionFormPage.tsx`

## Phase 6: Polish & Cleanup (Ongoing)
- [x] Remove Bootstrap imports
- [x] Remove unused CSS files
- [x] Update `main.tsx` (remove Bootstrap CSS)
- [x] Optimize Tailwind bundle
- [x] Test all responsive breakpoints
- [ ] Cross-browser testing
- [ ] Performance audit

## Phase 7: Deployment
- [ ] Merge to staging branch
- [ ] Full QA testing
- [ ] Deploy to production
- [ ] Monitor for issues
- [ ] Remove Bootstrap from `package.json`

---

## Migration Priority

1. **High Priority** (do first): CategoryPage, UnitPage, Layout
2. **Medium Priority**: ItemsPage, UsersPage, Forms
3. **Low Priority**: Dashboard, IssueDetails (most complex)

## Notes
- Keep Bootstrap installed during migration
- Can run both Bootstrap and Tailwind simultaneously
- Test each component after migration
- Commit frequently with small PRs

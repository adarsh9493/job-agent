#!/usr/bin/env python
# Job Search + Application Script - Skill 2
# Rules framework for search -> eligibility -> queue (one role per company, round-robin) -> tailor -> apply -> log.
# Data:      data/state/state.json, data/applications/current/ + history/
# Sweep:     skills/job-search/scripts/sweep.py
# Tailoring: skills/tailoring/scripts/build_all.py, render_pdf.py, verify_pdf.py, match_score.py
# Apply:     the `application-fill` skill (skills/application-fill/SKILL.md) driving the
#            Playwright MCP browser tools - this script owns the rules, not the browser.

import json
import os
import sys
import datetime
import shutil

# ============================================================================
# Configuration & Constants
# ============================================================================

# H-1B ineligibility patterns
H1B_INELIGIBLE = [
    r'no sponsorship',
    r'us.?persons? only',
    r'security clearance',
    r'contract.*?c2c',
    r'manager.*?role',
    r'people.*?manager',
]

# Automotive industry companies (from companies.md)
AUTOMOTIVE_COMPANIES = [
    'General Motors', 'Ford', 'Toyota', 'Honda', 'Nissan', 'Hyundai', 'Kia',
    'Bosch', 'Magna', 'Valeo', 'Lear', 'ZF', 'DENSO', 'Aptiv', 'Rivian',
    'PACCAR', 'Navistar', 'Panasonic', 'Magna', 'Mercedes-Benz', 'BMW',
    'Audi', 'Jaguar', 'Land Rover', 'Volvo', 'Infiniti', 'Acura',
    'Lexus', 'Buick', 'GMC', ' Cadillac',
    'Waymo', 'Nuro', 'Motional', 'Zoox', 'Torc', 'Aurora', 'Stack AV',
    'Bot Auto', 'Wayve', 'Waabi', 'Pronto', 'Gatik', 'Kodiak', 'Outrider',
]

# Test-only role names (user is tester, not developer)
TEST_ROLE_KEYWORDS = [
    'test', 'validation', 'verification', 'integration', 'hilsil mil',
    'reliability', 'dvp&r', 'quality', 'automation', 'sensors',
    'ecu', 'can', 'calibration', 'hilm', 'mil', 'sil'
]

DEVELOPER_ROLE_KEYWORDS = [
    'software engineer', 'developer', 'full stack', 'frontend',
    'backend', 'web', 'android', 'ml', 'algorithm', 'research',
    'platform', 'sre', 'devops', 'data science'
]

# Round-robin sweep (user-approved 2026-10-17) - no per-company caps.
SWEEP_POLICY = {
    'one_per_company_per_round': True,
    'min_days_between': 3,           # spacing guard; 0 = off
    'session_budget': 12,            # soft applications-per-session cap
    'order': 'least_recently_applied',
}

# Ford exclusion (user is current employer via Actalent)
MANUAL_APPLY_COMPANIES = {'Ford Motor Company'}

# Freshness filter: preferred ≤24h, fallback ≤7d, never >7d
FRESHNESS_PREFERRED_DAYS = 1
FRESHNESS_FALLBACK_DAYS = 7
FRESHNESS_HARD_CEILING_DAYS = 7

# ============================================================================
# Core Functions
# ============================================================================


def is_h1b_ineligible(job_data):
    """Check if job is ineligible for H-1B based on ineligibility patterns."""
    job_text = str(job_data).lower()
    for pattern in H1B_INELIGIBLE:
        if pattern.lower() in job_text:
            return True
    return False


def is_test_role(role_title):
    """Check if role is a tester role (not developer)."""
    title_lower = role_title.lower()
    # Check for developer roles - disqualify
    for dev_keyword in DEVELOPER_ROLE_KEYWORDS:
        if dev_keyword.lower() in title_lower:
            return False
    # Check for test roles - qualify
    for test_keyword in TEST_ROLE_KEYWORDS:
        if test_keyword.lower() in title_lower:
            return True
    # Default: keep role (consult sweep.py and companies.md filtering)
    return True


def is_automotive_industry(company, business_line=None):
    """Check if company/role falls under automotive industry filter."""
    company_upper = company.upper()
    # Direct automotive companies
    if any(ac in company_upper for ac in AUTOMOTIVE_COMPANIES):
        return True
    # If business line is provided, check it
    if business_line:
        bl_upper = business_line.upper()
        # Critical Materials = automotive IN, Redwood Energy = automotive OUT
        if 'CRITICAL MATERIALS' in bl_upper:
            return True
        if 'REDDWOOD ENERGY' in bl_upper or 'GRID' in bl_upper or 'BESS' in bl_upper:
            return False
    # Default: check companies.md for verdict
    return None  # Let companies.md decide


def is_cooling(days_since_last_applied, min_days_between=None):
    """Sweep spacing guard - True when a company was applied to too recently.

    There are no per-company caps any more; the only per-company limit is this
    spacing guard (default 3 days; pass 0 to disable the guard).
    """
    if min_days_between is None:
        min_days_between = SWEEP_POLICY['min_days_between']
    if not min_days_between or days_since_last_applied is None:
        return False
    return days_since_last_applied < min_days_between


def calculate_freshness(posted_date):
    """Calculate freshness score based on posting date."""
    if not posted_date:
        return 0  # Unknown date = low freshness

    try:
        # Parse posted date
        if isinstance(posted_date, str):
            # Try common date formats
            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    posted = datetime.datetime.strptime(posted_date, fmt)
                    break
                except ValueError:
                    continue
        else:
            posted = posted_date

        now = datetime.datetime.now()
        days_old = (now - posted).days

        if days_old <= FRESHNESS_PREFERRED_DAYS:
            return 1.0  # Preferred freshness
        elif days_old <= FRESHNESS_FALLBACK_DAYS:
            return 0.5  # Fallback freshness
        elif days_old <= FRESHNESS_HARD_CEILING_DAYS:
            return 0.2  # Near hard ceiling
        else:
            return 0  # Beyond hard ceiling
    except (ValueError, TypeError):
        return 0


def filter_by_eligibility(job_data):
    """Apply all eligibility filters to a job."""
    # H-1B sponsorship check
    if is_h1b_ineligible(job_data):
        return False, 'ineligible_h1b'

    # Role type check (tester vs developer)
    role_title = job_data.get('title', '')
    if not is_test_role(role_title):
        return False, 'developer_role'

    # Industry filter
    company = job_data.get('company', '')
    business_line = job_data.get('business_line', '')
    industry_result = is_automotive_industry(company, business_line)
    if industry_result is False:
        return False, 'non_automotive'
    if industry_result is None:
        # Need to check companies.md - defer to that logic
        return True, 'defer_industry'

    return True, 'eligible'


def update_state_after_application(company, job_title, job_id, state):
    """Update state.json after a job is applied."""
    state['applications_this_session'] += 1
    state['session_stats']['applied'] += 1

    # Update queue status
    for q in state['queue']:
        if q.get('company') == company and q.get('title') == job_title:
            q['status'] = 'applied - manual'
            q['applied_date'] = datetime.datetime.now().strftime('%Y-%m-%d')

    # Update the sweep's per-company last-applied date (use sweep.py)
    # Update cooling.md per the policy

    with open('data/state/state.json', 'w') as f:
        json.dump(state, f, indent=2)


def move_folder_to_history(current_folder, history_folder):
    """Move application folder from current/ to history/."""
    current_path = os.path.join('data/applications/current', current_folder)
    history_path = os.path.join('data/applications/history', current_folder)

    if os.path.isdir(current_path):
        shutil.move(current_path, history_path)
        return True
    return False


def refill_queue(state, sweep_result=None):
    """Reset the round's queue entries to 'queued' for the next sweep round."""
    # This would integrate with the search functionality
    # For now, reset queue statuses to 'queued'
    for q in state['queue']:
        q['status'] = 'queued'

    # Reset applications_this_session for new cycle
    state['applications_this_session'] = 0

    with open('data/state/state.json', 'w') as f:
        json.dump(state, f, indent=2)


# ============================================================================
# Execution Entry Point
# ============================================================================

def main():
    """Main entry point for Skill 2 - Job Search + Application."""
    print("=== Skill 2: Job Search + Application ===")
    print("Loading framework...")

    # Load current state
    state_path = 'data/state/state.json'
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = json.load(f)
        print(f"  Queue: {len(state['queue'])} entries")
        print(f"  applications_this_session: {state['applications_this_session']}")
    else:
        print("  WARNING: state.json not found")
        state = {'queue': [], 'applications_this_session': 0, 'session_stats': {'applied': 0, 'skipped': 0, 'failed': 0}}

    # Apply the sweep spacing check (integrate with sweep.py)
    # ... (would call sweep.py in production)

    # Apply Ford exclusion
    if any(company in MANUAL_APPLY_COMPANIES for company in [q.get('company', '') for q in state['queue']]):
        print("  Ford Motor Company excluded per user directive")

    # Main flow: search → queue → tailor → apply → log → refill
    print("\nFlow: search → queue (one/company, round-robin) → tailor → apply → log → next round")
    print("      no per-company caps | 3-day spacing guard | session budget ~12 | automotive-first filter")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())


# This script owns the RULES: search, eligibility/industry/tester filter, round-robin sweep
# (no caps; 3-day spacing guard), freshness, queue management, state.json updates,
# folder moves (current -> history) and the next sweep round.
#
# The browser work is NOT here. The actual submission is performed by the `application-fill`
# skill (skills/application-fill/SKILL.md) using the Playwright MCP browser tools
# (browser_navigate / browser_click / browser_type / browser_file_upload / ...). The agent
# loads that skill and drives Chrome directly, following its Greenhouse/Ashby/Lucid lessons
# and the mandatory 2-pass pre-submit review.
#
# The sweep order + spacing come from skills/job-search/scripts/sweep.py; resume-vs-JD match scoring
# comes from skills/tailoring/scripts/match_score.py.

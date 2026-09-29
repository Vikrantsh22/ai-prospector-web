import os
import sqlite3
import json
from flask import Flask, render_template, request, redirect, url_for, flash
​app = Flask(name)
app.secret_key = "cute-prospector-secret-key"
DB_PATH = os.path.join(os.path.dirname(file), "prospector.db")
​AI_NEED_INFO = {
"missed_call_followup": {"label": "Call Helper Bot", "emoji": "📞"},
"ai_chatbot": {"label": "Website Chat Pal", "emoji": "💬"},
"appointment_automation": {"label": "Smart Booking", "emoji": "📅"},
"review_automation": {"label": "Review Booster", "emoji": "⭐"},
"social_media_automation": {"label": "Social Spark", "emoji": "✨"},
}
​MOCK_BUSINESSES = [
{"name": "Riverside Dental", "industry": "Dental", "city": "Austin", "state": "TX",
"website": "riversidedental.com", "phone": "(512) 555-0142",
"review_count": 23, "rating": 4.8, "age_years": 8, "size": "2-10",
"has_online_booking": False, "has_live_chat": False, "has_contact_form": True,
"instagram_last_post_days": 240, "phone_is_primary_cta": True, "owner": "Dr. Sarah Chen"},
​{"name": "Blue Oak Landscaping", "industry": "Landscaping", "city": "Portland", "state": "OR",
"website": "blueoaklandscaping.com", "phone": "(503) 555-0198",
"review_count": 87, "rating": 4.9, "age_years": 12, "size": "10-50",
"has_online_booking": False, "has_live_chat": False, "has_contact_form": True,
"instagram_last_post_days": 15, "phone_is_primary_cta": True, "owner": "Marcus Webb"},
​{"name": "Bright Path Yoga", "industry": "Fitness", "city": "Boulder", "state": "CO",
"website": "brightpathyoga.com", "phone": "(303) 555-0111",
"review_count": 156, "rating": 4.9, "age_years": 6, "size": "2-10",
"has_online_booking": True, "has_live_chat": False, "has_contact_form": True,
"instagram_last_post_days": 3, "phone_is_primary_cta": False, "owner": "Priya Nair"},
​{"name": "Sunset Auto Repair", "industry": "Automotive", "city": "Phoenix", "state": "AZ",
"website": "sunsetautorepair.com", "phone": "(602) 555-0133",
"review_count": 412, "rating": 4.6, "age_years": 22, "size": "10-50",
"has_online_booking": False, "has_live_chat": False, "has_contact_form": False,
"instagram_last_post_days": 900, "phone_is_primary_cta": True, "owner": "Dave Kowalski"},
​{"name": "Magnolia Bakery & Cafe", "industry": "Food & Beverage", "city": "Charleston", "state": "SC",
"website": "magnoliabakerycafe.com", "phone": "(843) 555-0188",
"review_count": 523, "rating": 4.7, "age_years": 11, "size": "10-50",
"has_online_booking": False, "has_live_chat": False, "has_contact_form": True,
"instagram_last_post_days": 4, "phone_is_primary_cta": False, "owner": "Mabel Thompson"}
]
​def analyze_ai_needs(raw):
needs = []
reasoning = []
if raw.get("phone_is_primary_cta") and not raw.get("has_online_booking"):
needs.append("missed_call_followup")
reasoning.append("Primary CTA is phone call without automated calendar fallback.")
if not raw.get("has_live_chat"):
needs.append("ai_chatbot")
reasoning.append("Has web presence without immediate conversational capture.")
if not raw.get("has_online_booking"):
needs.append("appointment_automation")
reasoning.append("Requires manual contact for booking appointments.")
if raw.get("age_years", 0) > 5 and raw.get("review_count", 0) < 50:
needs.append("review_automation")
reasoning.append(f"Operating {raw['age_years']} yrs with only {raw['review_count']} reviews.")
if raw.get("instagram_last_post_days", 0) > 60:
needs.append("social_media_automation")
reasoning.append(f"Social feed resting for {raw['instagram_last_post_days']} days.")
return needs, " ".join(reasoning)
​def get_db():
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON;")
return conn
​def init_db():
with get_db() as conn:
conn.executescript("""
CREATE TABLE IF NOT EXISTS accounts (
account_id INTEGER PRIMARY KEY AUTOINCREMENT,
business_name TEXT NOT NULL,
industry TEXT,
city TEXT,
state TEXT,
country TEXT DEFAULT 'US',
website TEXT,
phone TEXT,
business_size TEXT,
lead_source TEXT NOT NULL DEFAULT 'google_maps',
source_date TEXT NOT NULL,
lawful_basis TEXT NOT NULL DEFAULT 'legitimate_interest_b2b',
potential_ai_need TEXT DEFAULT '[]',
ai_need_reasoning TEXT,
account_status TEXT NOT NULL DEFAULT 'prospect',
created_at TEXT DEFAULT CURRENT_TIMESTAMP,
CHECK (account_status IN ('prospect','enriched','queued','contacted',
'engaged','meeting_booked','proposal_sent','closed_won',
'closed_lost','disqualified','suppressed','nurture'))
);
​CREATE TABLE IF NOT EXISTS contacts (
contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
account_id INTEGER NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
full_name TEXT,
job_title TEXT,
email TEXT,
phone TEXT,
email_opt_out INTEGER DEFAULT 0,
email_opt_out_at TEXT,
contact_status TEXT NOT NULL DEFAULT 'active',
CHECK (contact_status IN ('active','bounced','unsubscribed','suppressed','do_not_contact'))
);
​CREATE TABLE IF NOT EXISTS suppression_list (
suppression_id INTEGER PRIMARY KEY AUTOINCREMENT,
email TEXT,
phone TEXT,
domain TEXT,
reason TEXT NOT NULL,
suppressed_at TEXT DEFAULT CURRENT_TIMESTAMP,
suppressed_by TEXT
);
​CREATE TABLE IF NOT EXISTS activities (
activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
account_id INTEGER REFERENCES accounts(account_id) ON DELETE CASCADE,
contact_id INTEGER REFERENCES contacts(contact_id),
activity_type TEXT NOT NULL,
sent_to_email TEXT,
body TEXT,
occurred_at TEXT DEFAULT CURRENT_TIMESTAMP
);
​CREATE TRIGGER IF NOT EXISTS trg_cascade_optout
AFTER UPDATE OF email_opt_out ON contacts
FOR EACH ROW
WHEN NEW.email_opt_out = 1 AND (OLD.email_opt_out IS NULL OR OLD.email_opt_out = 0)
BEGIN
INSERT INTO suppression_list (email, reason, suppressed_by)
VALUES (NEW.email, 'unsubscribe', 'web_guard');
​UPDATE contacts
SET contact_status = 'unsubscribed',
email_opt_out_at = CURRENT_TIMESTAMP
WHERE contact_id = NEW.contact_id;
​UPDATE accounts
SET account_status = 'suppressed'
WHERE account_id = NEW.account_id;
END;
​CREATE TRIGGER IF NOT EXISTS trg_enforce_suppression
BEFORE INSERT ON activities
FOR EACH ROW
WHEN NEW.activity_type IN ('email_sent','call_outbound')
AND (
EXISTS (SELECT 1 FROM suppression_list WHERE LOWER(email) = LOWER(NEW.sent_to_email))
OR EXISTS (SELECT 1 FROM contacts WHERE contact_id = NEW.contact_id AND email_opt_out = 1)
)
BEGIN
SELECT RAISE(ABORT, 'BLOCKED: Friend is resting on the quiet list 🛑');
END;
""")
​cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM accounts")
if cur.fetchone()[0] == 0:
for b in MOCK_BUSINESSES:
needs, reasoning = analyze_ai_needs(b)
cur.execute("""
INSERT INTO accounts (
business_name, industry, city, state, website, phone, business_size,
source_date, potential_ai_need, ai_need_reasoning, account_status
) VALUES (?, ?, ?, ?, ?, ?, ?, date('now'), ?, ?, 'prospect')
""", (
b["name"], b["industry"], b["city"], b["state"], b["website"],
b["phone"], b["size"], json.dumps(needs), reasoning
))
acc_id = cur.lastrowid
cur.execute("""
INSERT INTO contacts (account_id, full_name, job_title, email, phone)
VALUES (?, ?, 'Owner / Founder', ?, ?)
""", (acc_id, b["owner"], f"hello@{b['website']}", b["phone"]))
conn.commit()
​init_db()
​@app.context_processor
def inject_metadata():
return dict(ai_need_info=AI_NEED_INFO)
​@app.route("/")
def pipeline():
status_filter = request.args.get("status", "all")
with get_db() as conn:
if status_filter != "all":
rows = conn.execute(
"SELECT * FROM accounts WHERE account_status = ? ORDER BY account_id DESC",
(status_filter,)
).fetchall()
else:
rows = conn.execute("SELECT * FROM accounts ORDER BY account_id DESC").fetchall()
​accounts = []
for r in rows:
acc = dict(r)
acc["needs"] = json.loads(acc["potential_ai_need"] or "[]")
accounts.append(acc)
​return render_template("pipeline.html", accounts=accounts, active_filter=status_filter)
​@app.route("/account/int:account_id")
def account_detail(account_id):
with get_db() as conn:
account = conn.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,)).fetchone()
if not account:
return "Account not found", 404
contacts = conn.execute("SELECT * FROM contacts WHERE account_id = ?", (account_id,)).fetchall()
​acc = dict(account)
acc["needs"] = json.loads(acc["potential_ai_need"] or "[]")
return render_template("detail.html", account=acc, contacts=[dict(c) for c in contacts])
​@app.route("/account/int:account_id/status", methods=["POST"])
def update_status(account_id):
new_status = request.form.get("status")
with get_db() as conn:
conn.execute("UPDATE accounts SET account_status = ? WHERE account_id = ?", (new_status, account_id))
conn.commit()
flash(f"Stage changed to {new_status.replace('_', ' ').title()}! ✨", "success")
return redirect(url_for("account_detail", account_id=account_id))
​@app.route("/contact/int:contact_id/opt-out", methods=["POST"])
def opt_out(contact_id):
account_id = request.form.get("account_id")
with get_db() as conn:
conn.execute("UPDATE contacts SET email_opt_out = 1 WHERE contact_id = ?", (contact_id,))
conn.commit()
flash("Friend placed on Quiet Mode. Trigger cascades updated the blacklist. 🌸", "info")
return redirect(url_for("account_detail", account_id=account_id))
​@app.route("/contact/int:contact_id/action", methods=["POST"])
def record_action(contact_id):
account_id = request.form.get("account_id")
action_type = request.form.get("action_type")
email = request.form.get("email")
​try:
with get_db() as conn:
conn.execute(
"INSERT INTO activities (account_id, contact_id, activity_type, sent_to_email, body) VALUES (?, ?, ?, ?, ?)",
(account_id, contact_id, action_type, email, f"Dispatched {action_type} via web interface")
)
conn.execute("UPDATE accounts SET account_status = 'contacted' WHERE account_id = ?", (account_id,))
conn.commit()
flash("Action logged and lead stage updated! 💌", "success")
except sqlite3.DatabaseError as e:
flash(str(e), "error")
​return redirect(url_for("account_detail", account_id=account_id))
​@app.route("/compliance")
def compliance():
with get_db() as conn:
rows = conn.execute("SELECT * FROM suppression_list ORDER BY suppressed_at DESC").fetchall()
return render_template("compliance.html", suppressed=[dict(r) for r in rows])
​if name == "main":
app.run(host="0.0.0.0", port=5000, debug=True)

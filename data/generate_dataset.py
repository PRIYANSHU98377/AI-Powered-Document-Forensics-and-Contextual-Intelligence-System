import os
import json
import random
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
GENUINE_DIR = DATA_DIR / "demo_case_genuine"
TAMPERED_DIR = DATA_DIR / "demo_case_tampered"

GENUINE_DIR.mkdir(parents=True, exist_ok=True)
TAMPERED_DIR.mkdir(parents=True, exist_ok=True)

def get_font(size=14, bold=False):
    # Try standard system fonts, fallback to default
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "calibrib.ttf" if bold else "calibri.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    return ImageFont.load_default()

def draw_signature(draw, x, y, width=150, height=50, color=(15, 25, 110), seed=42):
    """Draw realistic cursive signature strokes."""
    rng = random.Random(seed)
    pts = [(x, y + height // 2)]
    curr_x = x
    while curr_x < x + width:
        step_x = rng.randint(8, 20)
        curr_x += step_x
        offset_y = rng.randint(-height // 2 + 5, height // 2 - 5)
        pts.append((curr_x, y + height // 2 + offset_y))
        # loop stroke
        if rng.random() > 0.6:
            pts.append((curr_x - rng.randint(3, 8), y + height // 2 + offset_y - rng.randint(10, 20)))
            pts.append((curr_x + rng.randint(2, 6), y + height // 2 + offset_y + rng.randint(5, 12)))
    
    # flourish underline
    pts.append((x + 10, y + height - 5))
    pts.append((x + width + 10, y + height - 8))
    
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i+1]], fill=color, width=2)

def draw_stamp(draw, center_x, center_y, radius=45, color=(180, 30, 30, 220), text="VERIFIED OFFICIAL"):
    """Draw a circular official seal/stamp."""
    x, y = center_x, center_y
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=color, width=3)
    draw.ellipse([x - radius + 6, y - radius + 6, x + radius - 6, y + radius - 6], outline=color, width=1)
    f = get_font(10, bold=True)
    draw.text((x - 30, y - 6), text, fill=color, font=f)
    draw.text((x - 18, y + 8), "★ ★ ★", fill=color, font=f)

def add_scan_effects(img: Image.Image, noise_sigma=3.0, blur=0.3, jpeg_quality=85) -> Image.Image:
    """Simulate authentic scanner/camera texture, slight tilt, and compression."""
    # Add subtle Gaussian noise
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, noise_sigma, arr.shape)
    noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    noisy_img = Image.fromarray(noisy_arr)
    
    if blur > 0:
        noisy_img = noisy_img.filter(ImageFilter.GaussianBlur(blur))
    return noisy_img

# ==========================================
# 1. ID CARD GENERATOR
# ==========================================
def generate_id_card(dest_path: Path, tampered=False):
    w, h = 800, 500
    img = Image.new("RGB", (w, h), (248, 249, 252))
    draw = ImageDraw.Draw(img)
    
    # Header banner
    draw.rectangle([0, 0, w, 70], fill=(24, 52, 94))
    f_title = get_font(22, bold=True)
    f_sub = get_font(12, bold=False)
    draw.text((30, 15), "REPUBLIC OF FORENSICA - NATIONAL IDENTITY CARD", fill=(255, 255, 255), font=f_title)
    draw.text((30, 45), "CITIZEN REGISTRATION & VERIFICATION DIVISION", fill=(200, 220, 240), font=f_sub)
    
    # Photo placeholder
    draw.rectangle([40, 100, 220, 320], fill=(210, 220, 230), outline=(100, 120, 140), width=2)
    draw.ellipse([95, 140, 165, 210], fill=(160, 175, 190))
    draw.polygon([(70, 280), (190, 280), (160, 225), (100, 225)], fill=(140, 155, 170))
    f_photo = get_font(11, bold=True)
    draw.text((80, 295), "PHOTO ID", fill=(80, 90, 100), font=f_photo)
    
    # Details
    f_lbl = get_font(12, bold=True)
    f_val = get_font(15, bold=False)
    f_id = get_font(18, bold=True)
    
    # ID Number
    draw.text((260, 100), "IDENTITY NUMBER:", fill=(100, 110, 125), font=f_lbl)
    draw.text((260, 120), "ID-9824-7120X", fill=(180, 20, 20), font=f_id)
    
    # Name
    draw.text((260, 155), "FULL NAME:", fill=(100, 110, 125), font=f_lbl)
    draw.text((260, 175), "RAHUL KUMAR SHARMA", fill=(20, 25, 30), font=f_val)
    
    # Father's name
    draw.text((260, 205), "FATHER'S NAME:", fill=(100, 110, 125), font=f_lbl)
    draw.text((260, 225), "VIKRAM SHARMA", fill=(20, 25, 30), font=f_val)
    
    # DOB (injected manipulation in tampered version!)
    draw.text((260, 255), "DATE OF BIRTH:", fill=(100, 110, 125), font=f_lbl)
    if tampered:
        # Altered DOB with mismatched font and background patch
        # Draw altered date patch
        draw.rectangle([258, 274, 400, 298], fill=(255, 255, 255))
        f_alt = get_font(16, bold=True)
        draw.text((260, 275), "1994-08-22", fill=(10, 15, 20), font=f_alt)
    else:
        draw.text((260, 275), "1988-04-15", fill=(20, 25, 30), font=f_val)
        
    # Gender & Issue Date
    draw.text((450, 255), "GENDER:", fill=(100, 110, 125), font=f_lbl)
    draw.text((450, 275), "MALE", fill=(20, 25, 30), font=f_val)
    
    draw.text((260, 310), "PERMANENT ADDRESS:", fill=(100, 110, 125), font=f_lbl)
    draw.text((260, 330), "Flat 402, Green Glen Heights, Outer Ring Road,", fill=(20, 25, 30), font=f_val)
    draw.text((260, 350), "Bellandur, Bangalore 560103", fill=(20, 25, 30), font=f_val)
    
    # Signature
    draw.text((600, 310), "CARDHOLDER SIGN:", fill=(100, 110, 125), font=f_lbl)
    draw_signature(draw, 580, 330, width=140, height=45, seed=101)
    
    # Seal
    draw_stamp(draw, 700, 180, radius=40, color=(30, 80, 160))
    
    # Footer
    draw.rectangle([0, 460, w, h], fill=(220, 225, 235))
    f_foot = get_font(10)
    draw.text((220, 475), "ISSUED: 10-JAN-2018 | EXPIRES: 09-JAN-2028 | SECURE CARD ID-9824", fill=(70, 80, 95), font=f_foot)
    
    img = add_scan_effects(img, noise_sigma=2.0)
    img.save(dest_path, quality=90)

# ==========================================
# 2. LOAN APPLICATION FORM (PDF)
# ==========================================
def generate_application_form(dest_path: Path, tampered=False):
    c = canvas.Canvas(str(dest_path), pagesize=A4)
    w, h = A4
    
    # Header
    c.setFillColor(colors.HexColor("#1A365D"))
    c.rect(0, h - 70, w, 70, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, h - 40, "HORIZON RETAIL BANK - LOAN APPLICATION FORM")
    c.setFont("Helvetica", 10)
    c.drawString(40, h - 55, "Personal Loan & Credit Assessment Application (Form 104-B)")
    
    # App Ref
    c.setFillColor(colors.HexColor("#2D3748"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, h - 90, "APPLICATION REF: APP-2026-9811")
    c.drawString(380, h - 90, "APPLICATION DATE: 2026-09-12")
    c.setLineWidth(1)
    c.setStrokeColor(colors.HexColor("#CBD5E0"))
    c.line(40, h - 98, w - 40, h - 98)
    
    # Section 1: Personal Details
    c.setFillColor(colors.HexColor("#2B6CB0"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, h - 120, "1. APPLICANT PERSONAL INFORMATION")
    
    labels = [
        ("Applicant Name:", "Rahul Kumar Sharma", 40, h - 145),
        ("Date of Birth:", "1988-04-15", 300, h - 145),
        ("Stated Age:", "38 Years", 460, h - 145),
        ("Father's Name:", "Vikram Sharma", 40, h - 175),
        ("Gender:", "Male", 300, h - 175),
        ("Marital Status:", "Married", 460, h - 175),
        ("National ID No:", "ID-9824-7120X", 40, h - 205),
        ("Contact Phone:", "+91 98450 12345", 300, h - 205),
        ("Email Address:", "rahul.sharma@apextech.com", 460, h - 205),
        ("Residential Address:", "Flat 402, Green Glen Heights, Outer Ring Road, Bangalore 560103", 40, h - 235),
    ]
    
    for lbl, val, x, y in labels:
        c.setFillColor(colors.HexColor("#718096"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y + 10, lbl)
        c.setFillColor(colors.HexColor("#1A202C"))
        c.setFont("Helvetica", 11)
        c.drawString(x, y - 4, val)
        
    # Section 2: Employment Details
    c.line(40, h - 260, w - 40, h - 260)
    c.setFillColor(colors.HexColor("#2B6CB0"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, h - 280, "2. EMPLOYMENT & FINANCIAL PARTICULARS")
    
    emp_labels = [
        ("Employer Name:", "Apex Tech Solutions Pvt Ltd", 40, h - 305),
        ("Designation:", "Lead Systems Architect", 300, h - 305),
        ("Monthly Net Salary:", "INR 125,000", 40, h - 335),
        ("Annual Gross Income:", "INR 1,800,000", 300, h - 335),
        ("Salary Account No:", "918273645012", 40, h - 365),
        ("Bank Name:", "State Horizon Bank", 300, h - 365),
        ("Loan Amount Requested:", "INR 500,000", 40, h - 395),
        ("Loan Tenure:", "36 Months", 300, h - 395),
    ]
    for lbl, val, x, y in emp_labels:
        c.setFillColor(colors.HexColor("#718096"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y + 10, lbl)
        c.setFillColor(colors.HexColor("#1A202C"))
        c.setFont("Helvetica", 11)
        c.drawString(x, y - 4, val)
        
    # Section 3: Declaration & Signature box
    c.line(40, h - 425, w - 40, h - 425)
    c.setFillColor(colors.HexColor("#2B6CB0"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, h - 445, "3. APPLICANT UNDERTAKING & DECLARATION")
    
    c.setFillColor(colors.HexColor("#4A5568"))
    c.setFont("Helvetica", 9)
    dec_text = (
        "I hereby declare that all particulars stated above are true and complete. "
        "I authorize Horizon Retail Bank to verify my credentials, credit bureau records, "
        "and contact my employer for verification."
    )
    c.drawString(40, h - 465, dec_text)
    
    # Signature Box
    c.rect(360, h - 560, 180, 70, stroke=1, fill=0)
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#A0AEC0"))
    c.drawString(370, h - 550, "Applicant Signature (Inside Box)")
    
    # Draw signature inside PDF
    # Draw vector signature lines
    c.setStrokeColor(colors.HexColor("#1A365D"))
    c.setLineWidth(1.5)
    p = c.beginPath()
    p.moveTo(380, h - 520)
    p.curveTo(400, h - 500, 420, h - 540, 440, h - 515)
    p.curveTo(460, h - 490, 480, h - 530, 500, h - 510)
    p.curveTo(510, h - 505, 520, h - 525, 530, h - 515)
    c.drawPath(p)
    c.line(385, h - 535, 525, h - 535)
    
    c.showPage()
    c.save()

# ==========================================
# 3. SALARY SLIP (PNG) - with altered digit in tampered
# ==========================================
def generate_salary_slip(dest_path: Path, tampered=False):
    w, h = 900, 650
    img = Image.new("RGB", (w, h), (252, 252, 254))
    draw = ImageDraw.Draw(img)
    
    # Company Header
    draw.rectangle([0, 0, w, 75], fill=(30, 41, 59))
    f_comp = get_font(20, bold=True)
    f_sub = get_font(11)
    draw.text((40, 15), "APEX TECH SOLUTIONS PRIVATE LIMITED", fill=(255, 255, 255), font=f_comp)
    draw.text((40, 45), "PAYSLIP FOR THE MONTH OF: SEPTEMBER 2026", fill=(190, 205, 225), font=f_sub)
    
    # Employee info box
    draw.rectangle([40, 95, w - 40, 180], outline=(203, 213, 225), width=1)
    f_hdr = get_font(11, bold=True)
    f_txt = get_font(13)
    
    draw.text((55, 105), "EMPLOYEE NAME:", fill=(100, 116, 139), font=f_hdr)
    draw.text((55, 125), "RAHUL KUMAR SHARMA", fill=(15, 23, 42), font=f_txt)
    
    draw.text((320, 105), "EMPLOYEE ID:", fill=(100, 116, 139), font=f_hdr)
    draw.text((320, 125), "EMP-44821", fill=(15, 23, 42), font=f_txt)
    
    draw.text((540, 105), "DESIGNATION:", fill=(100, 116, 139), font=f_hdr)
    draw.text((540, 125), "Lead Systems Architect", fill=(15, 23, 42), font=f_txt)
    
    draw.text((55, 145), "BANK ACCOUNT NO:", fill=(100, 116, 139), font=f_hdr)
    draw.text((55, 160), "918273645012", fill=(15, 23, 42), font=f_txt)
    
    draw.text((320, 145), "DAYS WORKED:", fill=(100, 116, 139), font=f_hdr)
    draw.text((320, 160), "30 Days", fill=(15, 23, 42), font=f_txt)
    
    draw.text((540, 145), "PAN / TAX ID:", fill=(100, 116, 139), font=f_hdr)
    draw.text((540, 160), "ABCDE1234F", fill=(15, 23, 42), font=f_txt)
    
    # Table headers
    draw.rectangle([40, 205, w - 40, 235], fill=(241, 245, 249))
    draw.text((55, 212), "EARNINGS COMPONENT", fill=(71, 85, 105), font=f_hdr)
    draw.text((300, 212), "AMOUNT (INR)", fill=(71, 85, 105), font=f_hdr)
    draw.text((480, 212), "DEDUCTIONS COMPONENT", fill=(71, 85, 105), font=f_hdr)
    draw.text((720, 212), "AMOUNT (INR)", fill=(71, 85, 105), font=f_hdr)
    
    # Line items
    items = [
        ("Basic Salary", "70,000", "Provident Fund (PF)", "8,400", 250),
        ("House Rent Allowance (HRA)", "35,000", "Professional Tax (PT)", "200", 280),
        ("Special Allowance", "20,000", "Income Tax (TDS)", "12,400", 310),
        ("Transport Allowance", "5,000", "Medical Insurance", "1,500", 340),
    ]
    for e_name, e_amt, d_name, d_amt, y in items:
        draw.text((55, y), e_name, fill=(51, 65, 85), font=f_txt)
        draw.text((300, y), e_amt, fill=(15, 23, 42), font=f_txt)
        draw.text((480, y), d_name, fill=(51, 65, 85), font=f_txt)
        draw.text((720, y), d_amt, fill=(15, 23, 42), font=f_txt)
        
    # Totals bar
    draw.rectangle([40, 380, w - 40, 425], fill=(226, 232, 240))
    f_total_lbl = get_font(12, bold=True)
    draw.text((55, 395), "GROSS EARNINGS:", fill=(15, 23, 42), font=f_total_lbl)
    
    # Net salary
    draw.rectangle([40, 445, w - 40, 495], fill=(238, 242, 255), outline=(199, 210, 254), width=1)
    draw.text((55, 460), "NET TAKE-HOME SALARY:", fill=(30, 27, 75), font=get_font(14, bold=True))
    
    if tampered:
        # Injected manipulation (a): amount digit changed in salary slip!
        # Instead of 130,000 / 125,000, Gross earnings shows 230,000 with a mismatched font and baseline
        draw.text((55 + 160, 395), "INR ", fill=(15, 23, 42), font=f_total_lbl)
        # Spliced digit '2' with distinct font, larger size (18pt bold vs standard) and slight shift
        f_spliced = get_font(19, bold=True)
        draw.text((55 + 195, 391), "2", fill=(5, 5, 5), font=f_spliced)
        draw.text((55 + 210, 395), "30,000", fill=(15, 23, 42), font=f_total_lbl)
        
        # Net salary altered: INR 207,500 instead of 107,500
        draw.text((320, 460), "INR ", fill=(30, 27, 75), font=get_font(14, bold=True))
        draw.text((360, 456), "2", fill=(10, 10, 40), font=get_font(19, bold=True))
        draw.text((375, 460), "07,500", fill=(30, 27, 75), font=get_font(14, bold=True))
    else:
        draw.text((55 + 160, 395), "INR 130,000", fill=(15, 23, 42), font=f_total_lbl)
        draw.text((320, 460), "INR 107,500", fill=(30, 27, 75), font=get_font(15, bold=True))
        
    draw.text((480, 395), "TOTAL DEDUCTIONS: INR 22,500", fill=(15, 23, 42), font=f_total_lbl)
    
    # HR Signature & Official Seal
    draw.text((55, 520), "AUTHORIZED SIGNATORY", fill=(100, 116, 139), font=f_hdr)
    draw_signature(draw, 50, 545, width=130, height=40, seed=77)
    draw_stamp(draw, 720, 550, radius=42, color=(30, 64, 175), text="APEX TECH CORP")
    
    img = add_scan_effects(img, noise_sigma=1.8)
    img.save(dest_path, quality=92)

# ==========================================
# 4. BANK STATEMENT (PDF)
# ==========================================
def generate_bank_statement(dest_path: Path, tampered=False):
    c = canvas.Canvas(str(dest_path), pagesize=letter)
    w, h = letter
    
    # Bank Logo & Header
    c.setFillColor(colors.HexColor("#0F172A"))
    c.rect(0, h - 80, w, 80, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h - 45, "STATE HORIZON BANK - ACCOUNT STATEMENT")
    c.setFont("Helvetica", 9)
    c.drawString(40, h - 62, "Quarterly Statement of Transactions | Cust Service: 1800-419-5555")
    
    # Account Summary Block
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, h - 105, "ACCOUNT HOLDER:")
    c.setFont("Helvetica", 10)
    c.drawString(160, h - 105, "Rahul Kumar Sharma")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, h - 122, "ACCOUNT NUMBER:")
    c.setFont("Helvetica", 10)
    c.drawString(160, h - 122, "918273645012")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, h - 139, "ACCOUNT TYPE:")
    c.setFont("Helvetica", 10)
    c.drawString(160, h - 139, "Privilege Savings Account")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(340, h - 105, "STATEMENT PERIOD:")
    c.setFont("Helvetica", 10)
    c.drawString(470, h - 105, "01-Jul-2026 to 30-Sep-2026")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(340, h - 122, "OPENING BALANCE:")
    c.setFont("Helvetica", 10)
    c.drawString(470, h - 122, "INR 84,500.00")
    
    # Table headers
    c.setFillColor(colors.HexColor("#F1F5F9"))
    c.rect(40, h - 185, w - 80, 24, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#334155"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(45, h - 172, "DATE")
    c.drawString(115, h - 172, "TRANSACTION DESCRIPTION")
    c.drawString(320, h - 172, "DEBIT (INR)")
    c.drawString(410, h - 172, "CREDIT (INR)")
    c.drawString(500, h - 172, "BALANCE (INR)")
    
    # Transactions list
    # Opening: 84,500
    # Jul 01: Salary +107,500 -> 192,000
    # Jul 05: Rent -32,000 -> 160,000
    # Jul 15: Utilities -4,500 -> 155,500
    # Aug 01: Salary +107,500 -> 263,000
    # Aug 08: Grocery -15,000 -> 248,000
    # Sep 01: Salary +107,500 -> 355,500
    # Sep 10: Credit Card -42,000 -> 313,500
    # Correct closing balance = 313,500.00
    
    txs = [
        ("01-Jul-2026", "SALARY CREDIT - APEX TECH", "", "107,500.00", "192,000.00"),
        ("05-Jul-2026", "NEFT - HOUSE RENT MR SINGH", "32,000.00", "", "160,000.00"),
        ("15-Jul-2026", "BESCOM ELECTRICITY BILL", "4,500.00", "", "155,500.00"),
        ("01-Aug-2026", "SALARY CREDIT - APEX TECH", "", "107,500.00", "263,000.00"),
        ("08-Aug-2026", "SUPERMARKET RETAIL PURCHASE", "15,000.00", "", "248,000.00"),
        ("01-Sep-2026", "SALARY CREDIT - APEX TECH", "", "107,500.00", "355,500.00"),
        ("10-Sep-2026", "HORIZON CREDIT CARD BILL", "42,000.00", "", "313,500.00"),
    ]
    
    y = h - 210
    c.setFont("Helvetica", 9)
    for dt, desc, dr, cr, bal in txs:
        c.setFillColor(colors.HexColor("#0F172A"))
        c.drawString(45, y, dt)
        
        # Tampered (c): pasted/whitened-over field on bank statement!
        # In tampered version, row 5 description has a whitened patch with mismatched background
        if tampered and "SUPERMARKET" in desc:
            # Draw whitened/pasted over rectangle with subtle background tint mismatch
            c.setFillColor(colors.HexColor("#EFF3F8"))
            c.rect(112, y - 4, 200, 18, fill=1, stroke=1)
            c.setFillColor(colors.HexColor("#1A202C"))
            c.setFont("Courier-Bold", 8.5)
            c.drawString(115, y, "CONSULTING FEE INFLOW (PASTED)")
            c.setFont("Helvetica", 9)
        else:
            c.drawString(115, y, desc)
            
        if dr:
            c.setFillColor(colors.HexColor("#DC2626"))
            c.drawString(320, y, dr)
        if cr:
            c.setFillColor(colors.HexColor("#16A34A"))
            c.drawString(410, y, cr)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.drawString(500, y, bal)
        
        # Thin row divider
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.setLineWidth(0.5)
        c.line(40, y - 6, w - 40, y - 6)
        y -= 25
        
    # Closing summary
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.rect(40, y - 40, w - 80, 35, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y - 22, "TOTAL DEBITS: INR 93,500.00")
    c.drawString(230, y - 22, "TOTAL CREDITS: INR 322,500.00")
    
    # Tampered (f): Closing balance not matching transactions!
    # Real balance: 313,500.00. Tampered balance: 485,000.00
    if tampered:
        c.drawString(420, y - 22, "CLOSING BAL: ")
        c.setFillColor(colors.HexColor("#B91C1C"))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(505, y - 22, "INR 485,000.00")
    else:
        c.drawString(420, y - 22, "CLOSING BAL: INR 313,500.00")
        
    c.showPage()
    c.save()

# ==========================================
# 5. UTILITY BILL (PNG) - with Address mismatch in tampered
# ==========================================
def generate_utility_bill(dest_path: Path, tampered=False):
    w, h = 800, 580
    img = Image.new("RGB", (w, h), (250, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Header
    draw.rectangle([0, 0, w, 70], fill=(21, 128, 61))
    draw.text((40, 15), "METROPOLITAN ELECTRICITY SUPPLY CORP", fill=(255, 255, 255), font=get_font(20, bold=True))
    draw.text((40, 45), "MONTHLY ELECTRICITY INVOICE & DEMAND NOTE", fill=(220, 252, 231), font=get_font(11))
    
    # Consumer particulars
    f_lbl = get_font(11, bold=True)
    f_val = get_font(13)
    
    draw.text((40, 95), "CONSUMER ID:", fill=(75, 85, 99), font=f_lbl)
    draw.text((40, 115), "RR-BLR-881903", fill=(17, 24, 39), font=f_val)
    
    draw.text((280, 95), "BILL NUMBER:", fill=(75, 85, 99), font=f_lbl)
    draw.text((280, 115), "BILL-2026-AUG-4491", fill=(17, 24, 39), font=f_val)
    
    draw.text((520, 95), "BILL DATE:", fill=(75, 85, 99), font=f_lbl)
    draw.text((520, 115), "15-Aug-2026", fill=(17, 24, 39), font=f_val)
    
    draw.text((40, 155), "CONSUMER NAME:", fill=(75, 85, 99), font=f_lbl)
    draw.text((40, 175), "Rahul K. Sharma", fill=(17, 24, 39), font=f_val)
    
    # Address field
    draw.text((40, 210), "SERVICE ADDRESS:", fill=(75, 85, 99), font=f_lbl)
    if tampered:
        # Tampered (g): address mismatch across utility bill and application!
        draw.text((40, 230), "Villa 12, Palm Meadows, Whitefield,", fill=(17, 24, 39), font=f_val)
        draw.text((40, 250), "Bangalore 560066", fill=(17, 24, 39), font=f_val)
    else:
        draw.text((40, 230), "Flat 402, Green Glen Heights, Outer Ring Road,", fill=(17, 24, 39), font=f_val)
        draw.text((40, 250), "Bellandur, Bangalore 560103", fill=(17, 24, 39), font=f_val)
        
    # Meter readings & charges
    draw.rectangle([40, 290, w - 40, 390], fill=(243, 244, 246), outline=(209, 213, 219), width=1)
    draw.text((55, 305), "PREVIOUS METER READING: 4,120 kWh", fill=(31, 41, 55), font=f_val)
    draw.text((55, 335), "CURRENT METER READING:  4,480 kWh", fill=(31, 41, 55), font=f_val)
    draw.text((55, 365), "NET UNITS CONSUMED:       360 kWh", fill=(31, 41, 55), font=f_val)
    
    draw.text((460, 305), "ENERGY CHARGES:   INR 3,240.00", fill=(31, 41, 55), font=f_val)
    draw.text((460, 335), "GOVT DUTY & TAX:  INR   310.00", fill=(31, 41, 55), font=f_val)
    draw.text((460, 365), "TOTAL AMOUNT DUE: INR 3,550.00", fill=(185, 28, 28), font=get_font(14, bold=True))
    
    # Paid Stamp
    draw_stamp(draw, 680, 480, radius=45, color=(22, 101, 52), text="PAID ONLINE")
    
    img = add_scan_effects(img, noise_sigma=2.2)
    img.save(dest_path, quality=90)

# ==========================================
# 6. SIGNED DECLARATION (PDF) - with cloned stamp & pasted signature in tampered
# ==========================================
def generate_declaration(dest_path: Path, tampered=False):
    c = canvas.Canvas(str(dest_path), pagesize=letter)
    w, h = letter
    
    # Metadata manipulation in tampered (h):
    if tampered:
        c.setAuthor("Adobe Acrobat Pro (v24.2.1 MacOS)")
        c.setCreator("Canva Design Studio Export v2.4")
        c.setSubject("Forensica Loan Declaration Tampered")
    else:
        c.setAuthor("Horizon Retail Bank System")
        c.setCreator("ReportLab PDF Library")
        
    # Title
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w / 2.0, h - 80, "AFFIDAVIT & FORMAL DECLARATION")
    c.setLineWidth(1)
    c.line(80, h - 90, w - 80, h - 90)
    
    # Body text
    c.setFillColor(colors.HexColor("#1F2937"))
    c.setFont("Helvetica", 11)
    lines = [
        "I, Rahul Kumar Sharma, son of Vikram Sharma, residing at",
        "Flat 402, Green Glen Heights, Outer Ring Road, Bangalore 560103,",
        "holding National Identity Card Number ID-9824-7120X, do hereby",
        "solemnly declare and affirm on this 12th day of September 2026:",
        "",
        "1. That all documents submitted for credit assessment, including my identity proof,",
        "   salary records, and banking transactions, are genuine, unmodified, and true.",
        "",
        "2. That I have not withheld any material fact or active liability that would impair",
        "   my financial capacity to repay credit extended by Horizon Retail Bank.",
        "",
        "3. That I acknowledge that misrepresentation or submission of altered records",
        "   shall warrant cancellation of approval and legal recourse.",
    ]
    y = h - 140
    for l in lines:
        c.drawString(80, y, l)
        y -= 22
        
    # Signature Box
    c.rect(80, h - 480, 220, 80, stroke=1, fill=0)
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#6B7280"))
    c.drawString(90, h - 470, "Signature of Deponent")
    
    # Tampered (e): signature from another source pasted onto declaration, with slight rectangular border and background tint!
    if tampered:
        # Cloned/Pasted signature with distinct sharp edge rectangular background
        c.setFillColor(colors.HexColor("#ECEEF5"))
        c.rect(85, h - 460, 210, 65, fill=1, stroke=1)
        c.setStrokeColor(colors.HexColor("#0A0A5C"))
        c.setLineWidth(2.2)
        p = c.beginPath()
        p.moveTo(100, h - 430)
        p.curveTo(130, h - 390, 160, h - 450, 190, h - 420)
        p.curveTo(220, h - 400, 240, h - 440, 270, h - 415)
        c.drawPath(p)
        c.line(105, h - 445, 275, h - 445)
    else:
        # Genuine signature matching applicant signature
        c.setStrokeColor(colors.HexColor("#1A365D"))
        c.setLineWidth(1.5)
        p = c.beginPath()
        p.moveTo(100, h - 430)
        p.curveTo(120, h - 410, 140, h - 450, 160, h - 425)
        p.curveTo(180, h - 400, 200, h - 440, 220, h - 420)
        p.curveTo(230, h - 415, 240, h - 435, 250, h - 425)
        c.drawPath(p)
        c.line(105, h - 445, 245, h - 445)
        
    # Tampered (d): Copy-moved stamp/seal!
    # Stamp 1 (Notary stamp)
    c.setStrokeColor(colors.HexColor("#991B1B"))
    c.circle(460, h - 440, 40)
    c.circle(460, h - 440, 35)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#991B1B"))
    c.drawCentredString(460, h - 435, "NOTARY PUBLIC")
    c.drawCentredString(460, h - 448, "GOVT OF FORENSICA")
    
    if tampered:
        # Exact clone copy-moved to another position (e.g. top right corner or duplicate witness stamp)
        c.circle(460, h - 540, 40)
        c.circle(460, h - 540, 35)
        c.drawCentredString(460, h - 535, "NOTARY PUBLIC")
        c.drawCentredString(460, h - 548, "GOVT OF FORENSICA")
        
    c.showPage()
    c.save()

# ==========================================
# 7. HARD NEGATIVES (Genuine compressed/blurred docs)
# ==========================================
def generate_hard_negative(dest_path: Path):
    """Heavy JPEG compression + scanner noise on a 100% genuine doc."""
    w, h = 800, 500
    img = Image.new("RGB", (w, h), (245, 246, 248))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w, 60], fill=(40, 50, 60))
    draw.text((30, 20), "UTILITY RECEIPT - COMPRESSED SCAN ARCHIVE", fill=(255, 255, 255), font=get_font(18, bold=True))
    draw.text((40, 100), "Consumer: Rahul Kumar Sharma", fill=(20, 20, 20), font=get_font(14))
    draw.text((40, 130), "Address: Flat 402, Green Glen Heights, Outer Ring Road, Bangalore 560103", fill=(20, 20, 20), font=get_font(14))
    draw.text((40, 160), "Amount Paid: INR 3,550.00", fill=(20, 20, 20), font=get_font(14))
    draw_stamp(draw, 600, 250, radius=40, color=(30, 70, 120), text="ARCHIVED SCAN")
    
    # Heavy compression + slight blur
    img = add_scan_effects(img, noise_sigma=5.0, blur=0.8)
    img.save(dest_path, quality=35)

def build_all():
    print("Generating GENUINE demo dataset...")
    generate_id_card(GENUINE_DIR / "id_card.png", tampered=False)
    generate_application_form(GENUINE_DIR / "application_form.pdf", tampered=False)
    generate_salary_slip(GENUINE_DIR / "salary_slip.png", tampered=False)
    generate_bank_statement(GENUINE_DIR / "bank_statement.pdf", tampered=False)
    generate_utility_bill(GENUINE_DIR / "utility_bill.png", tampered=False)
    generate_declaration(GENUINE_DIR / "declaration.pdf", tampered=False)
    generate_hard_negative(GENUINE_DIR / "hard_negative_scan.jpg")
    
    print("Generating TAMPERED demo dataset...")
    generate_id_card(TAMPERED_DIR / "id_card.png", tampered=True)
    generate_application_form(TAMPERED_DIR / "application_form.pdf", tampered=False)
    generate_salary_slip(TAMPERED_DIR / "salary_slip.png", tampered=True)
    generate_bank_statement(TAMPERED_DIR / "bank_statement.pdf", tampered=True)
    generate_utility_bill(TAMPERED_DIR / "utility_bill.png", tampered=True)
    generate_declaration(TAMPERED_DIR / "declaration.pdf", tampered=True)
    generate_hard_negative(TAMPERED_DIR / "hard_negative_scan.jpg")
    
    manipulations = {
        "case_id": "demo_tampered_case",
        "applicant": "Rahul Kumar Sharma",
        "ground_truth_manipulations": [
            {
                "id": "M1",
                "document": "salary_slip.png",
                "type": "font_mismatch_digit_alteration",
                "description": "Amount digit changed in salary slip (Gross earnings 230,000 instead of 130,000 with distinct font size/stroke)",
                "target_field": "gross_earnings",
                "expected_category": "POTENTIAL_MANIPULATION",
                "region_hint": {"page": 1, "x": 210, "y": 390, "w": 80, "h": 35}
            },
            {
                "id": "M2",
                "document": "id_card.png",
                "type": "cross_doc_dob_conflict",
                "description": "DOB altered on ID card (1994-08-22) vs application form (1988-04-15)",
                "target_field": "dob",
                "expected_category": "POTENTIAL_MANIPULATION",
                "region_hint": {"page": 1, "x": 258, "y": 274, "w": 145, "h": 30}
            },
            {
                "id": "M3",
                "document": "bank_statement.pdf",
                "type": "background_whitened_patch",
                "description": "Pasted/whitened-over field on bank statement with rectangular background luminance mismatch",
                "target_field": "transaction_row",
                "expected_category": "POTENTIAL_MANIPULATION",
                "region_hint": {"page": 1, "x": 112, "y": 420, "w": 180, "h": 20}
            },
            {
                "id": "M4",
                "document": "declaration.pdf",
                "type": "copy_move_cloned_stamp",
                "description": "Copy-moved duplicate notary stamp/seal cloned in declaration",
                "target_field": "notary_stamp",
                "expected_category": "POTENTIAL_MANIPULATION",
                "region_hint": {"page": 1, "x": 420, "y": 500, "w": 80, "h": 80}
            },
            {
                "id": "M5",
                "document": "declaration.pdf",
                "type": "pasted_signature_discontinuity",
                "description": "Signature from another source pasted onto declaration with sharp edge and background discontinuity",
                "target_field": "signature",
                "expected_category": "POTENTIAL_MANIPULATION",
                "region_hint": {"page": 1, "x": 85, "y": 400, "w": 210, "h": 65}
            },
            {
                "id": "M6",
                "document": "bank_statement.pdf",
                "type": "intra_doc_balance_arithmetic_mismatch",
                "description": "Closing balance (INR 485,000.00) does not match arithmetic sum of opening balance + credits - debits (INR 313,500.00)",
                "target_field": "closing_balance",
                "expected_category": "POTENTIAL_MANIPULATION",
                "region_hint": {"page": 1, "x": 420, "y": 640, "w": 150, "h": 30}
            },
            {
                "id": "M7",
                "document": "utility_bill.png",
                "type": "cross_doc_address_conflict",
                "description": "Address mismatch: utility bill shows Palm Meadows, Whitefield 560066 vs application Green Glen Heights, Bellandur 560103",
                "target_field": "address",
                "expected_category": "POTENTIAL_MANIPULATION",
                "region_hint": {"page": 1, "x": 40, "y": 230, "w": 300, "h": 40}
            },
            {
                "id": "M8",
                "document": "declaration.pdf",
                "type": "pdf_metadata_modification_anomaly",
                "description": "PDF metadata shows editor software tag (Adobe Acrobat Pro / Canva Export)",
                "target_field": "metadata",
                "expected_category": "POTENTIAL_MANIPULATION",
                "region_hint": {"page": 1, "x": 0, "y": 0, "w": 100, "h": 100}
            }
        ]
    }
    with open(DATA_DIR / "manipulations.json", "w") as f:
        json.dump(manipulations, f, indent=2)
    print("Dataset generation completed! manipulations.json saved.")

if __name__ == "__main__":
    build_all()

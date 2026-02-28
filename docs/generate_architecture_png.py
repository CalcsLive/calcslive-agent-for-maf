from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG = (248, 250, 252)

COLORS = {
    "lane": (226, 232, 240),
    "cloud_box": (219, 234, 254),
    "mcp_box": (204, 251, 241),
    "exec_box": (254, 243, 199),
    "text": (15, 23, 42),
    "arrow": (30, 41, 59),
    "dash": (71, 85, 105),
    "red_dash": (220, 38, 38),
    "badge": (59, 130, 246),
    "badge_text": (255, 255, 255),
}

def rect(draw, box, fill, outline=(100, 116, 139), width=2, r=14):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def center_text(draw, box, text, font, fill=COLORS["text"]):
    x1, y1, x2, y2 = box
    tw, th = draw.multiline_textbbox((0, 0), text, font=font, align="center")[2:]
    cx = (x1 + x2 - tw) // 2
    cy = (y1 + y2 - th) // 2
    draw.multiline_text((cx, cy), text, font=font, fill=fill, align="center")

def arrow(draw, p1, p2, color=COLORS["arrow"], width=3, dashed=False, bi_directional=False):
    x1, y1 = p1
    x2, y2 = p2
    if dashed:
        steps = 18
        for i in range(steps):
            if i % 2 == 0:
                a1 = i / steps
                a2 = (i + 1) / steps
                sx = x1 + (x2 - x1) * a1
                sy = y1 + (y2 - y1) * a1
                ex = x1 + (x2 - x1) * a2
                ey = y1 + (y2 - y1) * a2
                draw.line((sx, sy, ex, ey), fill=color, width=width)
    else:
        draw.line((x1, y1, x2, y2), fill=color, width=width)

    def draw_head(px1, py1, px2, py2):
        vx = px2 - px1
        vy = py2 - py1
        mag = (vx * vx + vy * vy) ** 0.5 or 1
        ux, uy = vx / mag, vy / mag
        px, py = -uy, ux
        size = 12
        p_left = (px2 - ux * size - px * size * 0.6, py2 - uy * size - py * size * 0.6)
        p_right = (px2 - ux * size + px * size * 0.6, py2 - uy * size + py * size * 0.6)
        draw.polygon([p_left, p_right, (px2, py2)], fill=color)

    draw_head(x1, y1, x2, y2)
    if bi_directional:
        draw_head(x2, y2, x1, y1)

def badge(draw, x, y, label, font):
    r = 14
    draw.ellipse((x - r, y - r, x + r, y + r), fill=COLORS["badge"])
    tw, th = draw.textbbox((0, 0), label, font=font)[2:]
    draw.text((x - tw // 2, y - th // 2 - 1), label, font=font, fill=COLORS["badge_text"])

def main():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        box_font = ImageFont.truetype("arial.ttf", 18)
        lane_font = ImageFont.truetype("arial.ttf", 20)
        warning_font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        title_font = ImageFont.load_default()
        box_font = ImageFont.load_default()
        lane_font = ImageFont.load_default()
        warning_font = ImageFont.load_default()

    # Title
    draw.text((30, 20), "CalcsLive Reference Architecture (Streamlit MVP & ODR Fallback)", fill=COLORS["text"], font=title_font)

    # Swimlanes
    lanes = [
        (20, 80, 1900, 340, "User + Orchestration (Cloud/Local Web)"),
        (20, 360, 1900, 640, "MCP Tool & API Layer"),
        (20, 660, 1900, 1040, "Execution Targets (Local + Backend)"),
    ]
    for x1, y1, x2, y2, label in lanes:
        rect(draw, (x1, y1, x2, y2), fill=COLORS["lane"], outline=(203, 213, 225), width=2, r=10)
        draw.text((x1 + 12, y1 + 10), label, fill=COLORS["text"], font=lane_font)

    # Cloud boxes
    user = (60, 160, 300, 260)
    orch = (380, 160, 660, 260)
    calc_agent = (740, 120, 1060, 200)
    excel_agent = (740, 240, 1060, 320)

    for b in [user, orch, calc_agent, excel_agent]:
        rect(draw, b, COLORS["cloud_box"])

    center_text(draw, user, "User\n(Streamlit Web Dashboard)", box_font)
    center_text(draw, orch, "Azure Agent\n(MAF Orchestrator)", box_font)
    center_text(draw, calc_agent, "Calc Agent logic", box_font)
    center_text(draw, excel_agent, "Excel Agent logic", box_font)

    # Control Arrows
    arrow(draw, (300, 210), (380, 210), bi_directional=True)
    arrow(draw, (660, 210), (740, 160))
    arrow(draw, (660, 210), (740, 280))

    # Tool / API boxes
    cl_api = (740, 440, 1060, 520)
    ex_bridge = (1140, 440, 1460, 520)
    ex_mcp = (1560, 440, 1860, 520)

    for b in [cl_api, ex_bridge, ex_mcp]:
        rect(draw, b, COLORS["mcp_box"])

    center_text(draw, cl_api, "CalcsLive API", box_font)
    center_text(draw, ex_bridge, "Local Excel Bridge\n(REST localhost:8001)", box_font)
    center_text(draw, ex_mcp, "Excel MCP Wrapper\n(Registered to Windows ODR)", box_font)

    # ODR Warning Line between ex_bridge and ex_mcp
    arrow(draw, (1480, 380), (1480, 620), color=COLORS["red_dash"], dashed=True, width=4)
    draw.text((1490, 400), "ODR execution blocked by Secure Boot", fill=COLORS["red_dash"], font=warning_font)
    draw.text((1490, 420), "TestMode policy in Dev Preview", fill=COLORS["red_dash"], font=warning_font)

    # Tool Arrows
    arrow(draw, (900, 200), (900, 440))
    arrow(draw, (1060, 280), (1200, 440))
    arrow(draw, (1060, 280), (1600, 440), dashed=True) # Intended path

    # Execution targets
    cl_backend = (740, 780, 1060, 880)
    ex_desktop = (1140, 780, 1460, 880)

    for b in [cl_backend, ex_desktop]:
        rect(draw, b, COLORS["exec_box"])

    center_text(draw, cl_backend, "CalcsLive Backend\n(Unit Engine + Article Store)", box_font)
    center_text(draw, ex_desktop, "Excel 2016 Pro Desktop", box_font)

    # Execution arrows
    arrow(draw, (900, 520), (900, 780))
    arrow(draw, (1300, 520), (1300, 780))
    arrow(draw, (1650, 520), (1400, 780))

    # Dashed returns
    arrow(draw, (950, 780), (950, 520), dashed=True, color=COLORS["dash"], width=2)
    arrow(draw, (1350, 780), (1350, 520), dashed=True, color=COLORS["dash"], width=2)
    arrow(draw, (1200, 440), (1050, 310), dashed=True, color=COLORS["dash"], width=2)
    arrow(draw, (950, 440), (950, 200), dashed=True, color=COLORS["dash"], width=2)
    arrow(draw, (740, 180), (660, 220), dashed=True, color=COLORS["dash"], width=2)
    arrow(draw, (740, 300), (660, 240), dashed=True, color=COLORS["dash"], width=2)

    # Workflow Badges
    badge_font = title_font
    badge(draw, 340, 180, "1", badge_font)
    badge(draw, 1100, 340, "2", badge_font)
    badge(draw, 870, 340, "3", badge_font)
    badge(draw, 980, 650, "4", badge_font)
    badge(draw, 1270, 650, "5", badge_font)
    badge(draw, 680, 280, "6", badge_font)

    # Side Annotations
    callout_x = 30
    callout_y = 930
    draw.text((callout_x, callout_y), "Key Concepts:", fill=COLORS["text"], font=title_font)
    draw.text((callout_x, callout_y + 30), "1. CalcsLive Article = Source of Truth", fill=COLORS["text"], font=lane_font)
    draw.text((callout_x, callout_y + 55), "2. Unit-aware compute centralized in CalcsLive", fill=COLORS["text"], font=lane_font)
    draw.text((callout_x, callout_y + 80), "3. Streamlit acts as cross-application System Utility Interface", fill=COLORS["text"], font=lane_font)

    # Legend
    draw.text((1460, 950), "Legend:", fill=COLORS["text"], font=lane_font)
    draw.rectangle((1460, 980, 1500, 1000), fill=COLORS["cloud_box"], outline=(100, 116, 139))
    draw.text((1510, 980), "Agent logic", fill=COLORS["text"], font=lane_font)
    draw.rectangle((1460, 1010, 1500, 1030), fill=COLORS["mcp_box"], outline=(100, 116, 139))
    draw.text((1510, 1010), "Tool / API Layer", fill=COLORS["text"], font=lane_font)
    draw.rectangle((1460, 1040, 1500, 1060), fill=COLORS["exec_box"], outline=(100, 116, 139))
    draw.text((1510, 1040), "Execution targets", fill=COLORS["text"], font=lane_font)

    out = "docs/architecture.png"
    img.save(out)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()

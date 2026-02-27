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


def arrow(draw, p1, p2, color=COLORS["arrow"], width=3, dashed=False):
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

    # Arrow head
    vx = x2 - x1
    vy = y2 - y1
    mag = (vx * vx + vy * vy) ** 0.5 or 1
    ux, uy = vx / mag, vy / mag
    px, py = -uy, ux
    size = 12
    p_left = (x2 - ux * size - px * size * 0.6, y2 - uy * size - py * size * 0.6)
    p_right = (x2 - ux * size + px * size * 0.6, y2 - uy * size + py * size * 0.6)
    draw.polygon([p_left, p_right, (x2, y2)], fill=color)


def badge(draw, x, y, label, font):
    r = 14
    draw.ellipse((x - r, y - r, x + r, y + r), fill=COLORS["badge"])
    tw, th = draw.textbbox((0, 0), label, font=font)[2:]
    draw.text((x - tw // 2, y - th // 2 - 1), label, font=font, fill=COLORS["badge_text"])


def main():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.load_default()
    box_font = ImageFont.load_default()
    lane_font = ImageFont.load_default()

    # Title
    draw.text((30, 20), "CalcsLive Reference Architecture (MAF + MCP + Windows Local Host/ODR)", fill=COLORS["text"], font=title_font)

    # Swimlanes
    lanes = [
        (20, 80, 1900, 340, "User + Orchestration (Cloud)"),
        (20, 360, 1900, 640, "MCP Tool Layer"),
        (20, 660, 1900, 1040, "Execution Targets (Local + Backend)"),
    ]
    for x1, y1, x2, y2, label in lanes:
        rect(draw, (x1, y1, x2, y2), fill=COLORS["lane"], outline=(203, 213, 225), width=2, r=10)
        draw.text((x1 + 12, y1 + 10), label, fill=COLORS["text"], font=lane_font)

    # Cloud boxes
    user = (80, 170, 260, 250)
    orch = (340, 150, 700, 270)
    calc = (820, 130, 1040, 230)
    excel_agent = (820, 245, 1040, 345)
    cad_agent = (820, 20 + 340, 1040, 120 + 340)  # near bottom edge of lane

    for b in [user, orch, calc, excel_agent, cad_agent]:
        rect(draw, b, COLORS["cloud_box"])

    center_text(draw, user, "User", box_font)
    center_text(draw, orch, "MAF Orchestrator\nAgent", box_font)
    center_text(draw, calc, "Calc Agent", box_font)
    center_text(draw, excel_agent, "Excel Agent", box_font)
    center_text(draw, cad_agent, "CAD Agent\n(optional)", box_font)

    # MCP boxes
    cl_mcp = (760, 430, 1080, 530)
    ex_mcp = (1130, 430, 1510, 530)
    cad_mcp = (1560, 430, 1880, 530)

    for b in [cl_mcp, ex_mcp, cad_mcp]:
        rect(draw, b, COLORS["mcp_box"])

    center_text(draw, cl_mcp, "CalcsLive MCP", box_font)
    center_text(draw, ex_mcp, "Excel MCP\n(Windows Local Host/ODR)", box_font)
    center_text(draw, cad_mcp, "FreeCAD MCP\n(Windows Local Host/ODR)\n(optional)", box_font)

    # Execution boxes
    cl_backend = (700, 780, 1140, 920)
    excel_desktop = (1180, 780, 1500, 920)
    freecad_desktop = (1540, 780, 1860, 920)

    for b in [cl_backend, excel_desktop, freecad_desktop]:
        rect(draw, b, COLORS["exec_box"])

    center_text(draw, cl_backend, "CalcsLive Backend\n(Unit Engine + Article Store)", box_font)
    center_text(draw, excel_desktop, "Excel Desktop", box_font)
    center_text(draw, freecad_desktop, "FreeCAD Desktop\n(optional)", box_font)

    # Solid control arrows
    arrow(draw, (260, 210), (340, 210))
    arrow(draw, (700, 190), (820, 180))
    arrow(draw, (700, 230), (820, 295))
    arrow(draw, (700, 255), (820, 390))

    # Tool invocation arrows
    arrow(draw, (930, 230), (920, 430))
    arrow(draw, (1040, 295), (1130, 480))
    arrow(draw, (1040, 390), (1560, 480))

    # Execution arrows
    arrow(draw, (920, 530), (920, 780))
    arrow(draw, (1320, 530), (1320, 780))
    arrow(draw, (1710, 530), (1710, 780))

    # Dashed return arrows
    arrow(draw, (980, 780), (980, 530), dashed=True, color=COLORS["dash"], width=2)
    arrow(draw, (1380, 780), (1380, 530), dashed=True, color=COLORS["dash"], width=2)
    arrow(draw, (1130, 500), (1040, 320), dashed=True, color=COLORS["dash"], width=2)
    arrow(draw, (900, 430), (900, 230), dashed=True, color=COLORS["dash"], width=2)
    arrow(draw, (830, 300), (700, 240), dashed=True, color=COLORS["dash"], width=2)
    arrow(draw, (840, 180), (700, 175), dashed=True, color=COLORS["dash"], width=2)

    # Numbered workflow badges
    badge_font = ImageFont.load_default()
    badge(draw, 300, 195, "1", badge_font)
    badge(draw, 1085, 360, "2", badge_font)
    badge(draw, 925, 330, "3", badge_font)
    badge(draw, 960, 650, "4", badge_font)
    badge(draw, 1360, 650, "5", badge_font)
    badge(draw, 760, 210, "6", badge_font)

    # Right-side callouts
    callout_x = 20
    callout_y = 930
    draw.text((callout_x, callout_y), "Key callouts:", fill=COLORS["text"], font=box_font)
    draw.text((callout_x, callout_y + 20), "- CalcsLive Article = Source of Truth", fill=COLORS["text"], font=box_font)
    draw.text((callout_x, callout_y + 40), "- Unit-aware compute centralized in CalcsLive", fill=COLORS["text"], font=box_font)
    draw.text((callout_x, callout_y + 60), "- Desktop access via Windows local host (ODR)", fill=COLORS["text"], font=box_font)

    # Legend
    draw.text((1460, 950), "Legend:", fill=COLORS["text"], font=box_font)
    draw.rectangle((1460, 970, 1500, 990), fill=COLORS["cloud_box"], outline=(100, 116, 139))
    draw.text((1510, 972), "Cloud agents", fill=COLORS["text"], font=box_font)
    draw.rectangle((1460, 995, 1500, 1015), fill=COLORS["mcp_box"], outline=(100, 116, 139))
    draw.text((1510, 997), "MCP tools", fill=COLORS["text"], font=box_font)
    draw.rectangle((1460, 1020, 1500, 1040), fill=COLORS["exec_box"], outline=(100, 116, 139))
    draw.text((1510, 1022), "Execution targets", fill=COLORS["text"], font=box_font)

    out = "docs/architecture.png"
    img.save(out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

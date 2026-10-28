import os
from fpdf import FPDF


class RTOPresentationPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(100, 116, 139)
        self.cell(90, 6, "SMART RTO TRAFFIC VIOLATION MONITORING SYSTEM", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", "", 8)
        self.cell(90, 6, "PURE SOFTWARE & COMPUTER VISION SYSTEM", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(203, 213, 225)
        self.set_line_width(0.3)
        self.line(15, 13, 195, 13)
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.3)
        self.line(15, 283, 195, 283)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(148, 163, 184)
        self.cell(90, 8, "Department of Computer Engineering / Electronics", new_x="RIGHT", new_y="TOP")
        self.cell(90, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")

    def section_title(self, num, title):
        self.ln(3)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(15, 23, 42)
        self.set_font("Helvetica", "B", 10.5)
        self.cell(180, 7, f" {num}. {title.upper()}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub_title(self, title):
        self.set_x(15)
        self.set_text_color(30, 58, 138)
        self.set_font("Helvetica", "B", 9)
        self.cell(180, 5.5, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_p(self, text):
        self.set_x(15)
        self.set_text_color(51, 65, 85)
        self.set_font("Helvetica", "", 8.5)
        self.multi_cell(180, 4.2, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def bullet_item(self, bold_prefix, text):
        self.set_x(15)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(15, 23, 42)
        self.write(4.2, f"- {bold_prefix} ")
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(51, 65, 85)
        self.write(4.2, text + "\n")
        self.ln(1.5)

    def qna_box(self, q_num, question, answer):
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.2)
        y = self.get_y()
        self.line(15, y, 195, y)
        self.set_xy(15, y + 1.5)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(15, 23, 42)
        self.multi_cell(180, 4.2, f"Q{q_num}: {question}", new_x="LMARGIN", new_y="NEXT")
        self.set_x(15)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(51, 65, 85)
        self.multi_cell(180, 4.2, f"Answer: {answer}", new_x="LMARGIN", new_y="NEXT")
        self.ln(2.5)


def generate_guide():
    pdf = RTOPresentationPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 16, 15)
    pdf.set_auto_page_break(auto=True, margin=16)

    # ---------------- PAGE 1: TITLE & SYSTEM OVERVIEW ----------------
    pdf.add_page()

    # Document Header Box
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(15, 16, 180, 24, "F")
    pdf.set_xy(18, 18)
    pdf.set_font("Helvetica", "B", 13.5)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(174, 7, "SMART RTO TRAFFIC RULE VIOLATION DETECTION SYSTEM", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(18)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(203, 213, 225)
    pdf.cell(174, 5, "Intelligent Computer Vision & Autonomous Violation Monitoring Platform", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(18)
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.cell(174, 4, "Pure Software Architecture: Virtual Stop-Line Analysis, YOLOv8 Vision & Automated E-Challan Engine", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(44)

    pdf.section_title(1, "Executive Summary & Architectural Paradigm")
    pdf.body_p(
        "Modern Intelligent Transportation Systems (ITS) have transitioned away from physical in-road sensors (such as inductive "
        "loops and infrared tripwires) due to high installation costs, asphalt degradation, and vulnerability to environmental damage. "
        "This project presents a 100% Software-Based Intelligent Video Analytics (IVA) Traffic Violation Detection & Monitoring System. "
        "The system executes real-time junction surveillance via an automated virtual signal controller synchronized with high-definition "
        "CCTV video feeds. The pipeline applies Region-of-Interest (ROI) Virtual Stop-Line tracking, Ultralytics YOLOv8 object detection, "
        "spatial centroid heuristic evaluation for triple riding, and Tesseract OCR with Indian registration syntax verification. "
        "The application runs completely self-contained on a standard workstation, eliminating all hardware wire dependencies."
    )

    pdf.section_title(2, "Hardware Tripwire vs. Modern Computer Vision Comparison")
    
    # Comparison Table
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(42, 6, "Evaluation Parameter", 1, new_x="RIGHT", new_y="TOP", align="L", fill=True)
    pdf.cell(68, 6, "Traditional In-Road Hardware (IR / Loops)", 1, new_x="RIGHT", new_y="TOP", align="L", fill=True)
    pdf.cell(70, 6, "Our Pure Software Computer Vision Architecture", 1, new_x="LMARGIN", new_y="NEXT", align="L", fill=True)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(51, 65, 85)
    comp_rows = [
        ("Deployment Cost", "High: Requires road cutting, wiring, and breadboard units.", "Zero In-Road Cost: Leverages existing municipal CCTV cameras."),
        ("Environmental Durability", "Vulnerable to dust, monsoon rains, vibrations, and asphalt wear.", "Immune to physical weathering; operates entirely at server layer."),
        ("Multi-Violation Capability", "Limited solely to binary line-crossing detection.", "Multi-class: Red Light, Triple Riding, Helmet, Speed estimation."),
        ("Maintenance & Reliability", "Frequent hardware breakdown and loose wire faults.", "High software uptime with automated crash-recovery daemons."),
    ]
    for row in comp_rows:
        pdf.cell(42, 5.2, row[0], 1, new_x="RIGHT", new_y="TOP", align="L")
        pdf.cell(68, 5.2, row[1], 1, new_x="RIGHT", new_y="TOP", align="L")
        pdf.cell(70, 5.2, row[2], 1, new_x="LMARGIN", new_y="NEXT", align="L")

    pdf.ln(2)

    pdf.section_title(3, "Software Architecture & Dataflow Pipeline")
    pdf.set_font("Courier", "", 7.2)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_text_color(30, 41, 59)
    block_diag = (
        "+---------------------------------------------------------------------------------------+\n"
        "| [Smart Signal Protocol Engine] ---> Automated Cycle: Green (8s) | Yellow (3s) | Red (8s)|\n"
        "+------------------------------------------+--------------------------------------------+\n"
        "                                           v\n"
        "+---------------------------------------------------------------------------------------+\n"
        "| [Live CCTV Video Ingestion] ---> 25 FPS Surveillance Stream + Virtual Stop-Line ROI    |\n"
        "+------------------------------------------+--------------------------------------------+\n"
        "                                           v\n"
        "+---------------------------------------------------------------------------------------+\n"
        "| [YOLOv8 Deep Learning Engine] ---> Multi-Class Object Detection (Vehicle / Person)     |\n"
        "| [Spatial Intersection Analytics] ---> Centroid-in-BBox Rider Density (Triple Riding)   |\n"
        "| [Adaptive ANPR Engine] ---> Bilateral Filter + Contour Crop + Tesseract OCR (Regex)   |\n"
        "+------------------------------------------+--------------------------------------------+\n"
        "                                           v\n"
        "+---------------------------------------------------------------------------------------+\n"
        "| [SQLite Persistence & RTO Portal] ---> Offender History, MVA E-Challan, Web Telemetry |\n"
        "+---------------------------------------------------------------------------------------+"
    )
    pdf.multi_cell(180, 3.2, block_diag, fill=True, new_x="LMARGIN", new_y="NEXT")

    # ---------------- PAGE 2: LIVE DEMO PROTOCOL & SCRIPT ----------------
    pdf.add_page()

    pdf.section_title(4, "Laptop Live Demonstration Guide (For Professor / Examiner)")
    pdf.body_p(
        "The system has been engineered to run completely on your laptop without any external hardware requirements. "
        "Follow this exact walkthrough during your presentation:"
    )

    pdf.bullet_item("System Launch (10 Seconds):", 
                    "Open terminal and execute 'python3 run.py'. Open browser at http://localhost:5000. Point out the top telemetry bar showing: Signal Phase countdown, Smart Controller: ACTIVE, and CCTV: LIVE FEED.")

    pdf.bullet_item("Demonstrating Lawful Traffic Flow (Green Phase):", 
                    "Observe the traffic signal in the GREEN state on screen. Note that vehicles cross the stop-line safely. Press [Spacebar] or click 'Vehicle Crosses Stop-Line' during green. Explain that the system recognizes lawful entry and records zero penalty.")

    pdf.bullet_item("Enforcing Red Light Violation (The Key Moment):", 
                    "Wait until the signal transitions to RED (or click 'Force RED'). Press [Spacebar] on the laptop. Immediately: (1) Synthesized 2.4kHz audio buzzer sounds through laptop speakers, (2) The stop-line sensor turns red, (3) Instant alert notifies the officer with vehicle number and detected violation.")

    pdf.bullet_item("Evidence Inspection & Bounding Boxes:", 
                    "Show the newly logged infraction row on the Dashboard. Click the evidence photo thumbnail to reveal the high-resolution surveillance snapshot with vehicle bounding box, speed indicator, and recognized number plate.")

    pdf.bullet_item("Motor Vehicles Act (MVA) Digital E-Challan:", 
                    "Click the 'E-Challan' button on the record. Display the legal violation document showing statutory section (e.g., Section 119/177 MVA), compounding fine amount, unique transaction ID, and official QR code.")

    pdf.bullet_item("Repeat Offender Accumulation (Vahan Registry):", 
                    "Navigate to 'Vahan Registry' and search 'MH15AB1234'. Demonstrate how the relational database groups all infractions under the single vehicle profile, compounding penalties for repeat violators.")

    pdf.bullet_item("Administrative Record Deletion:", 
                    "Navigate to 'Violations' and demonstrate the delete action [X]. Show how erroneous test rows or images are permanently unlinked and deleted from disk with a single click.")

    pdf.ln(1)
    pdf.section_title(5, "Technical Components & Algorithmic Stack")
    
    pdf.bullet_item("Neural Network Backbone:", "Ultralytics YOLOv8n (Nano) convolutional model pretrained on COCO dataset, optimized for CPU inference speed (<40ms latency) without requiring discrete GPU acceleration.")
    pdf.bullet_item("Triple Riding Association Heuristic:", "Computes spatial overlap IoU (Intersection over Union) between 'person' bounding box centroids and 'motorcycle' bounding boxes. Greater than two riders triggers an automatic violation.")
    pdf.bullet_item("Optical Character Recognition (OCR):", "Preprocesses license plate regions using adaptive bilateral filtering and Otsu thresholding, followed by Tesseract OCR syntax verification matching Indian state codes (e.g., MH, DL, KA).")
    pdf.bullet_item("Backend Framework & Audio Engine:", "Python Flask asynchronous REST framework paired with Web Audio API for browser-synthesized piezo warning sirens.")

    # ---------------- PAGE 3: VIVA VOCE QUESTIONS & ANSWERS ----------------
    pdf.add_page()

    pdf.section_title(6, "Top 10 Technical Viva Voce Examination Questions & Answers")

    qna_list = [
        ("Why did you choose a pure software Computer Vision approach over physical Arduino / IR sensors?",
         "In real-world Smart City projects, physical road-cut sensors (like IR tripwires or magnetic loops) are obsolete because asphalt heat, monsoon rains, and road repairs damage them rapidly. In contrast, our camera-based Virtual Stop-Line architecture utilizes existing junction CCTV infrastructure, requiring zero physical road modification and offering multi-violation detection capabilities."),

        ("How does the system establish a 'Virtual Stop-Line' without physical sensors?",
         "The computer vision engine defines a calibrated geometric 2D Region-of-Interest (ROI) line across the intersection roadway. Using frame-by-frame object centroid tracking, when a vehicle bounding box crosses this vector while the internal signal state register equals 'RED', a line-crossing event is mathematically triggered."),

        ("Why was YOLOv8 chosen over traditional algorithms like Haar Cascades or Background Subtraction?",
         "Traditional edge detection or Haar Cascades suffer from severe false positive rates under shadow variations, headlamp glare, and complex traffic occlusion. YOLOv8 utilizes an anchor-free CSPDarknet architecture that analyzes global context across the entire image in a single forward pass, providing superior Mean Average Precision (mAP) at real-time speeds (>25 FPS)."),

        ("How does the Triple Riding detection algorithm work mathematically?",
         "The detector outputs bounding boxes (x1, y1, x2, y2) and class IDs for all objects in the frame. For every detected 'motorcycle' bounding box, the algorithm counts how many 'person' bounding box centroids fall within the expanded coordinate boundary [x1 - delta, y1 - delta, x2 + delta, y2 + delta]. If count > 2, a Triple Riding infraction is flagged."),

        ("What happens when a vehicle's number plate is damaged, dirty, or unreadable?",
         "Rather than guessing or hallucinating incorrect characters, the extracted string is validated against standard Indian registration patterns using regular expressions (^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$). If it fails, the record is stored as 'Number Plate Not Clearly Detected' and queued for manual human verification, preserving evidentiary integrity."),

        ("Why is helmet violation categorized as 'Potential Violation' in the prototype?",
         "Standard COCO-trained YOLO models include 'person' and 'motorcycle' classes, but do not possess dedicated 'helmet' / 'no_helmet' labels. To maintain academic and scientific honesty, our prototype designates helmet infractions as potential violations requiring verification unless fine-tuned weights (models/helmet.pt) are provided."),

        ("What database architecture is implemented and why SQLite?",
         "SQLite is a self-contained, serverless, transactional SQL engine that stores the entire relational database in a single portable file (data/rto.db). It supports full ACID compliance, foreign-key constraints linking vehicles and timestamped violations, and eliminates the runtime dependency of external database servers."),

        ("How does the system handle signal timing and synchronization?",
         "The backend runs an autonomous signal protocol daemon executing statutory phase cycles: Green (8s), Yellow (3s), and Red (8s). The controller exposes REST endpoints (/api/hardware/signal) enabling seamless manual overrides (Force RED, Force GREEN) for emergency vehicle clearance simulations."),

        ("How does the E-Challan module calculate fines and repeat offenses?",
         "When an infraction is committed, the system queries the 'vehicles' table. If the vehicle already has registered infractions, the fine structure under the Motor Vehicles Act automatically scales, and compounding penal notices are compiled into an official digital notice with QR verification."),

        ("What is the scalability and edge-deployment roadmap for this system?",
         "1. Deploy edge AI nodes (NVIDIA Jetson Orin Nano / RK3588) on physical traffic poles. 2. Integrate with the national VAHAN / SARATHI vehicle database API for automated SMS challan dispatch. 3. Implement high-speed ANPR cameras with infrared night-vision illuminators.")
    ]

    for idx, (q, a) in enumerate(qna_list, 1):
        pdf.qna_box(idx, q, a)

    # Output to project root
    output_path = "RTO_System_Presentation_Guide.pdf"
    pdf.output(output_path)
    print(f"Successfully generated: {output_path}")


if __name__ == "__main__":
    generate_guide()

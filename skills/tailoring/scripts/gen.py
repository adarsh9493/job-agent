# -*- coding: utf-8 -*-
"""Tailoring generator: builds a resume + cover letter HTML from the master resume content
(data/master/master resume.docx). Only real, master-derived content is used; nothing invented.
Usage:  python gen.py <job_key>
"""
import sys, os

TEMP = r"C:\Users\adars\AppData\Local\Temp\opencode"

# ---------------------------------------------------------------- shared CSS
RES_CSS = """
      @page { size: Letter; margin: 0.55in 0.65in; }
      * { box-sizing: border-box; }
      body { font-family: Arial, Helvetica, "Segoe UI", sans-serif; font-size: 10pt; line-height: 1.32; color: #111; margin: 0; }
      h1 { font-size: 19pt; margin: 0 0 2pt; letter-spacing: 0.4pt; }
      .contact { font-size: 9.5pt; color: #333; margin-bottom: 9pt; }
      h2 { font-size: 10.5pt; text-transform: uppercase; letter-spacing: 1pt; border-bottom: 1pt solid #111; padding-bottom: 2pt; margin: 11pt 0 5pt; }
      p { margin: 0; }
      .skills { margin: 0; padding: 0; list-style: none; }
      .skills li { margin: 0 0 2pt; }
      .proj { margin: 0 0 5pt; }
      .proj-name { font-weight: bold; }
      .proj-meta { color: #333; font-size: 9pt; }
      .job { margin-bottom: 8pt; }
      .job-head { display: flex; justify-content: space-between; gap: 8pt; }
      .job-title { font-weight: bold; font-size: 10.5pt; }
      .job-meta { white-space: nowrap; color: #333; font-size: 9.5pt; }
      .job-company { font-style: italic; }
      .sub { font-weight: bold; font-size: 9.5pt; margin: 3pt 0 0; }
      .sub-meta { font-weight: normal; font-style: italic; color: #333; }
      ul.bullets { margin: 2pt 0 0; padding-left: 15pt; }
      ul.bullets li { margin-bottom: 1.5pt; }
      .edu { margin-bottom: 4pt; }
"""

COV_CSS = """
      @page { size: Letter; margin: 0.75in; }
      * { box-sizing: border-box; }
      body { font-family: Arial, Helvetica, "Segoe UI", sans-serif; font-size: 10.5pt; line-height: 1.4; color: #111; margin: 0; }
      .header { margin-bottom: 14pt; }
      .name { font-size: 16pt; font-weight: bold; margin-bottom: 2pt; }
      .contact { font-size: 9pt; color: #333; }
      .date { margin-bottom: 12pt; }
      .recipient { margin-bottom: 12pt; }
      p { margin: 0 0 9pt; }
      .signoff { margin-top: 12pt; }
"""

CONTACT = "(714) 728-9684 &nbsp;|&nbsp; adarsh.9493@gmail.com &nbsp;|&nbsp; Farmington Hills, MI &nbsp;|&nbsp; linkedin.com/in/adarsh-ramanujapuram-a1ab9740"

# ---------------------------------------------------------------- shared content (all master-derived)
PROJECTS = {
    "fnv3": dict(
        name="FNV3 &amp; FNV3.X &mdash; Ford / Lincoln vehicle programs (5 vehicle programs)",
        meta="Lead Software Validation Engineer &bull; May 2022 &ndash; Present &bull;",
        desc="Component-, system- and vehicle-level validation on component benches, mini benches, partial/full test benches and production vehicles; CAN/CAN-FD signal monitoring (ValueCAN4, RadMoon), data acquisition and system-response analysis, Python automation, QNX/Android AOS integration, root-cause analysis.",
    ),
    "fnv4": dict(
        name="FNV4 &mdash; Ford next-generation vehicle program",
        meta="Validation lead, 14-member distributed team &bull; Jul 2024 &ndash; Aug 2025 &bull;",
        desc="Owned localization and system validation execution; authored ~3,100 functional and system-level test cases; built reusable Python automation templates; HLD/POC validation with system architects; defect-trend and quality-metric reporting.",
    ),
    "fnv2": dict(
        name="FNV2 &ndash; SYNC 4 &mdash; Ford F-150, Mustang Mach-E, F-150 Lightning",
        meta="Lead Software Validation Engineer &bull; Feb 2021 &ndash; May 2022 &bull;",
        desc="End-to-end component-, system- and vehicle-level validation of the SYNC 4 platform in bench and real-vehicle environments; CAN signal validation, test-case design from Agile requirements, defect investigation and fix verification.",
    ),
    "gm_hil": dict(
        name="GM Global A &amp; Global B HIL Validation &mdash; General Motors platforms (Danlaw Inc.)",
        meta="Software Validation Engineer &ndash; HIL &bull; Sep 2017 &ndash; Feb 2021 &bull;",
        desc="Built and configured HIL benches with Danlaw Mx-Suite/MxVDev and Vector VN-1630; CAN/CAN-FD communication with physical ECUs, DBC/ARXML signal configuration, regression validation, ECU response analysis, RCA with LG Electronics, Magna and Valeo.",
    ),
    "pisquare": dict(
        name="In-Vehicle Infotainment &amp; ADAS Feature Validation (Pi-Square Technologies)",
        meta="Infotainment Test Engineer &bull; Apr 2017 &ndash; Sep 2017 &bull;",
        desc="In-vehicle validation of HUD, Bluetooth and cluster connectivity features and ADAS-related features; CAN bus monitoring and debugging with Vehicle Spy, CANoe and CANalyzer; requirements traceability in IBM DOORS.",
    ),
}

EXPERIENCE = """
    <div class="job">
      <div class="job-head">
        <span class="job-title">Lead Software Validation Engineer</span>
        <span class="job-meta">Feb 2021 &ndash; Present</span>
      </div>
      <div class="job-company">Ford Motor Company (contract via Actalent) &mdash; Dearborn, MI</div>

      <div class="sub">FNV3 &amp; FNV3.X <span class="sub-meta">&bull; May 2022 &ndash; Present</span></div>
      <ul class="bullets">
        <li>Led component-, system- and vehicle-level validation across <strong>5 Ford and Lincoln vehicle programs</strong>, supporting production releases through testing on component benches, mini benches, partial/full test benches and production vehicles.</li>
        <li>Configured and prepared component- and system-level test benches &mdash; required hardware, software, communication interfaces and test configurations &mdash; to support feature validation and stability testing across bench and vehicle environments.</li>
        <li>Executed CAN/CAN-FD signal monitoring, data acquisition and system-response analysis during component, bench and vehicle testing to evaluate feature behavior against expected requirements, using ValueCAN4 and RadMoon.</li>
        <li>Developed and maintained <strong>Python-based automation</strong> for component-level functional, regression and stability testing, improving test repeatability and reducing manual execution effort.</li>
        <li>Executed automated stability and regression runs across bench and vehicle environments, analyzing test results, system behavior, failure patterns, quality metrics and defect trends and presenting findings to feature owners, system architects and program leadership.</li>
        <li>Performed <strong>PRA, RCA, Fault Tree Analysis, Fishbone Analysis and 5-Why analysis</strong> to identify failure mechanisms, assess defect risk and drive resolution of complex system-level issues.</li>
        <li>Validated system behavior and state transitions across QNX and Android AOS environments, analyzing host/guest OS interactions and their impact on integrated vehicle-system functionality.</li>
        <li>Partnered with feature owners, system architects, developers and suppliers to analyze system-level failures, troubleshoot CAN/system issues and validate corrective actions across integrated automotive systems.</li>
        <li>Built an AI-assisted testing workflow (GitHub Copilot, OpenCode, VS Code) covering build retrieval, flashing, test setup, sanity testing and execution support, and documented reusable frameworks and execution guidelines in Confluence.</li>
      </ul>

      <div class="sub">FNV4 <span class="sub-meta">&bull; Jul 2024 &ndash; Aug 2025</span></div>
      <ul class="bullets">
        <li>Led localization and system validation activities for a distributed <strong>14-member engineering team</strong>, establishing execution priorities, reviewing test results and system behavior, and presenting validation status and defect trends in program reviews.</li>
        <li>Authored approximately <strong>3,100 functional and system-level test cases</strong> from requirements and architectural specifications, covering HMI and system layers.</li>
        <li>Collaborated with system architects and software developers during <strong>HLD reviews and POC validation</strong>, translating architectural requirements into test strategies and identifying system integration gaps.</li>
        <li>Developed reusable Python automation templates using slash-based and data-driven testing methodologies, standardizing automation practice across component teams; developed Python automation for AOS Power Management stability and regression testing.</li>
        <li>Performed root-cause investigation for AOSP-OS anomalies including system resets, service crashes and black-screen conditions, collaborating with development and architecture teams to validate fixes.</li>
      </ul>

      <div class="sub">FNV2 &ndash; SYNC 4 <span class="sub-meta">&bull; Feb 2021 &ndash; May 2022</span></div>
      <ul class="bullets">
        <li>Led end-to-end component-, system- and vehicle-level validation of the SYNC 4 platform across the Ford <strong>F-150, Mustang Mach-E and F-150 Lightning</strong> programs, evaluating feature behavior across bench and real-vehicle environments.</li>
        <li>Configured and validated bench and vehicle test environments, monitoring system behavior and communication signals and troubleshooting integration issues during end-to-end testing.</li>
        <li>Performed CAN-based signal and communication validation during component and vehicle testing, analyzing system responses and investigating communication-related defects.</li>
        <li>Designed and executed functional and system-level test cases from Agile requirements and user stories, maintaining traceability from requirements through validation, defect investigation and fix verification.</li>
        <li>Led vehicle-level testing and defect investigation, collaborating with feature and development teams to analyze system behavior, reproduce failures, identify root causes and validate software fixes.</li>
      </ul>
    </div>

    <div class="job">
      <div class="job-head">
        <span class="job-title">Software Validation Engineer &ndash; HIL</span>
        <span class="job-meta">Sep 2017 &ndash; Feb 2021</span>
      </div>
      <div class="job-company">Danlaw Inc. &mdash; Novi, MI</div>

      <div class="sub">Project: General Motors &mdash; Global A &amp; Global B Platforms <span class="sub-meta">&bull; Sep 2017 &ndash; Feb 2021</span></div>
      <ul class="bullets">
        <li>Developed and configured subsystem simulation models in <strong>Danlaw Mx-Suite/MxVDev</strong> for HIL benches, supporting real-time simulation, ECU interaction and requirements-based validation of automotive system functions.</li>
        <li>Configured and integrated Mx-Suite HIL environments with <strong>Vector VN-1630</strong> interfaces, establishing CAN/CAN-FD communication between the simulation environment and physical ECUs for subsystem- and system-level validation.</li>
        <li>Developed and executed HIL test cases and validation scenarios for GM Global A and Global B architectures using CAN/CAN-FD communication, DBC/ARXML signal configuration, signal monitoring and ECU response analysis.</li>
        <li>Utilized Mx-Suite for model-based and simulation-based testing, test execution, signal acquisition, data analysis and regression validation, evaluating ECU/system responses against expected behavior.</li>
        <li>Developed reusable automation and monitoring solutions in Mx-Suite, creating repeatable test scenarios and regression coverage to improve execution efficiency and validation consistency.</li>
        <li>Performed <strong>root-cause analysis</strong> of HIL validation failures and system integration defects, collaborating with OEM and supplier engineering teams including <strong>LG Electronics, Magna and Valeo</strong> to troubleshoot issues and coordinate corrective actions.</li>
      </ul>
    </div>

    <div class="job">
      <div class="job-head">
        <span class="job-title">Infotainment Test Engineer</span>
        <span class="job-meta">Apr 2017 &ndash; Sep 2017</span>
      </div>
      <div class="job-company">Pi-Square Technologies &mdash; Farmington Hills, MI</div>
      <ul class="bullets">
        <li>Performed in-vehicle validation of infotainment and ADAS-related features &mdash; HUD, Bluetooth and cluster connectivity systems &mdash; verifying system behavior against requirements.</li>
        <li>Used CAN tools including Vehicle Spy, CANoe and CANalyzer for signal analysis, bus monitoring and debugging of vehicle network issues.</li>
        <li>Managed requirements and traceability using IBM DOORS; maintained requirements-based test procedures aligned with evolving features.</li>
      </ul>
    </div>
"""

EDUCATION = """
    <div class="edu"><strong>M.S. Mechanical Engineering</strong> &mdash; California State University, Fullerton &mdash; 2017</div>
    <div class="edu"><strong>B.Tech. Aeronautical Engineering</strong> &mdash; JNTU, Hyderabad, India &mdash; 2014</div>
"""

# ---------------------------------------------------------------- per-job tailoring
JOBS = {
    "harbinger_pt": dict(
        folder="Harbinger_Motors_Senior_Test_Integration_Engineer_Powertrain_5205318007_2026-10-13",
        summary=(
            "Systems integration and validation engineer with 9+ years delivering production-ready embedded and vehicle systems, "
            "with deep hands-on experience in powertrain and vehicle-level test. I run component-, subsystem-, system- and "
            "vehicle-level development and validation testing end to end: preparing and configuring component, mini and full test "
            "benches, setting up sensors, data-acquisition and measurement equipment, monitoring CAN/CAN-FD signal behavior, and "
            "writing Python- and LabVIEW-based test automation built for repeatability, efficiency and safety. Strong at "
            "reproducing and characterizing failures, driving root-cause analysis on electrical, mechanical and software "
            "integration issues, and documenting test setups, procedures and results for compliance and knowledge transfer. "
            "Comfortable partnering with system architects, developers and suppliers to close integration gaps and validate "
            "corrective actions, including HIL/SIL environments (Danlaw Mx-Suite, Vector VN-1630) and multi-OS embedded "
            "platforms (QNX, Android AOSP)."
        ),
        skills=[
            ("Validation &amp; Integration", "Component-, System- &amp; Vehicle-Level Development &amp; Validation Testing &bull; Electrical, Mechanical &amp; Software Integration &bull; Requirements-Based Validation &bull; HLD Review &amp; POC Validation"),
            ("Test Benches, Rigs &amp; Instrumentation", "Component, Mini &amp; Full Test Bench Preparation &amp; Bring-Up &bull; Sensor / Signal Monitoring &amp; Data Acquisition (DAQ) &bull; Digital Multimeter, Oscilloscopes, DAQ Boards &bull; Measurement &amp; System-Response Analysis"),
            ("Test Automation &amp; Software", "Python Test Automation (OOP) &bull; NI LabVIEW &bull; MATLAB/Simulink &bull; Automated Regression &amp; Stability Testing &bull; Slash-Based &amp; Data-Driven Test Frameworks"),
            ("HIL / SIL Validation", "Danlaw Mx-Suite / MxVDev &bull; Vector VN-1630 &bull; Model-Based &amp; Simulation-Based Testing &bull; Real-Time ECU Interaction &bull; DBC / ARXML Signal Configuration"),
            ("Vehicle Networks &amp; Diagnostics", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; UDS &amp; DoIP &bull; ValueCAN3/4, RadMoon, Rad-Galaxy &bull; CANoe / CANalyzer, Vehicle Spy"),
            ("Failure Analysis &amp; Quality", "Failure Reproduction &amp; Characterization &bull; Root-Cause Analysis (PRA/RCA, FTA, Fishbone, 5-Why) &bull; Defect Triage &amp; Trend Analysis &bull; ISO 26262 Functional-Safety Awareness"),
            ("Delivery &amp; Tools", "OEM&ndash;Supplier Collaboration (LG, Magna, Valeo) &bull; Distributed Team Leadership (14+) &bull; Agile / Scrum &bull; Python, Git, JIRA, JAMA, IBM DOORS, Confluence &bull; Microcontrollers, Arduino"),
        ],
        project_order=["fnv3", "fnv4", "fnv2", "gm_hil", "pisquare"],
        cover_company="Harbinger Motors",
        cover_addr="Garden Grove, California",
        cover_paras=[
            "I'm applying for the Senior Test Integration Engineer, Powertrain role at Harbinger. Building the test setup itself &mdash; the bench, the instrumentation and the software that runs it &mdash; is the part of validation I've enjoyed most over nine years, and the job description reads like the work I already do.",
            "At Ford I run component-, system- and vehicle-level validation across five Ford and Lincoln vehicle programs, on component benches, mini benches, partial and full test benches, and production vehicles. Preparing those benches is my day-to-day: configuring the hardware, the communication interfaces and the test configuration, then bringing the setup up so a feature can actually be exercised and measured. I capture and analyze data from them &mdash; monitoring CAN and CAN-FD traffic with ValueCAN4 and RadMoon, watching signals and system responses against the requirements &mdash; and when something misbehaves I reproduce it, characterize the failure and chase the root cause down with a multimeter or an oscilloscope until we understand what broke and why. I write and maintain Python automation for functional, regression and stability testing, and I've built reusable, data-driven test frameworks that other component teams use. I use LabVIEW, MATLAB/Simulink and Mx-Suite the same way &mdash; to drive hardware, run scenarios and keep testing repeatable.",
            "Before Ford I spent three and a half years at Danlaw building and running HIL benches for GM's Global A and Global B platforms &mdash; subsystem simulation models in Mx-Suite/MxVDev, integrated with Vector VN-1630 interfaces so the simulation could talk to physical ECUs over CAN/CAN-FD. That's where I learned to debug the electrical, mechanical and software layers together, and to follow problems across company lines with teams like LG Electronics, Magna and Valeo. I document what I build &mdash; test procedures, setups, results &mdash; because a test setup nobody else can run isn't worth much. An early-stage EV company standing up its powertrain test capability from scratch is exactly where that matters.",
            "I'd welcome the chance to talk about how I could help build out Harbinger's powertrain test lab. Thank you for your time and consideration.",
        ],
    ),
    "kodiak": dict(
        folder="Kodiak_Hardware_Quality_Industrialization_Engineer_4321392009_2026-10-13",
        summary=(
            "Validation and systems engineer with 9+ years in automotive, including 3.5 years of HIL validation with General Motors "
            "and 5.5 years of component-, system- and vehicle-level validation at Ford. My work is built around finding and fixing "
            "the cause of hardware and software failures: reproducing and characterizing failures on benches and production "
            "vehicles, running PRA, RCA, Fault Tree, Fishbone and 5-Why analysis, tracking defect trends and quality metrics, and "
            "driving corrective actions to closure with internal teams and suppliers including LG Electronics, Magna and Valeo. I "
            "set test parameters and pass/fail limits with test and design teams, author test cases from requirements (about 3,100 "
            "in one program), and document processes so they can be repeated by anyone. Comfortable being the first person in a "
            "role, defining the process rather than inheriting it, and reporting status and risk to engineering and program "
            "leadership."
        ),
        skills=[
            ("Problem Solving &amp; Root Cause", "PRA &bull; RCA &bull; Fault Tree Analysis (FTA) &bull; Fishbone &bull; 5-Why &bull; Failure Reproduction &amp; Characterization &bull; Corrective-Action Verification"),
            ("Quality &amp; Data Analysis", "Defect Triage &bull; Failure Patterns &amp; Defect-Trend Analysis &bull; Quality-Metric Reporting &bull; Requirements-to-Test Traceability &bull; Test Results Review &amp; Reporting"),
            ("Test Strategy &amp; Validation", "Pass/Fail Limit &amp; Test-Parameter Definition &bull; Requirements-Based Test-Case Authoring (~3,100 in one program) &bull; Regression &amp; Stability Testing &bull; Component-, System- &amp; Vehicle-Level Validation &bull; Field-Style Failure Investigation on Production Vehicles"),
            ("Supplier &amp; Cross-Functional", "OEM&ndash;Supplier Collaboration (LG Electronics, Magna, Valeo) &bull; Issue Resolution Across Disciplines &bull; Program Status &amp; Risk Reporting &bull; Distributed Team Leadership (14+) &bull; Agile / Scrum"),
            ("Test &amp; Measurement", "Test-Bench / HIL Configuration (Danlaw Mx-Suite, Vector VN-1630) &bull; Data Acquisition &amp; Signal Monitoring &bull; Digital Multimeter, Oscilloscopes, DAQ Boards &bull; CAN / CAN-FD / LIN / Automotive Ethernet"),
            ("Software &amp; Tools", "Python Automation (OOP) &bull; MATLAB/Simulink &bull; LabVIEW &bull; JIRA, JAMA, IBM DOORS, Confluence, TestRail &bull; Git"),
        ],
        project_order=["fnv3", "gm_hil", "fnv4", "fnv2", "pisquare"],
        cover_company="Kodiak Robotics",
        cover_addr="Mountain View, California",
        cover_paras=[
            "I'd like to be considered for the Hardware Quality Industrialization Engineer role at Kodiak. I'll be straight with you: my career has been on the validation side rather than in a supplier-quality function, but the core of that job &mdash; finding out why hardware fails, proving it, and making sure the fix sticks &mdash; is what I've done every day for nine years.",
            "At Ford I run component-, system- and vehicle-level validation across five vehicle programs, on benches and on production vehicles. When something fails I reproduce it, characterize the failure and work it down with PRA, RCA, Fault Tree, Fishbone and 5-Why analysis, then track the defect trend and quality metrics and present them to feature owners, architects and program leadership. I also help set test parameters and pass/fail limits with the test and design teams, and I author test cases from requirements &mdash; around 3,100 of them in one program &mdash; with traceability back to the requirement so nothing gets closed on a hunch.",
            "Before Ford I spent three and a half years at Danlaw on HIL benches for GM's Global A and Global B platforms, where a lot of my root-cause work ran across company lines: I debugged integration failures with OEM and supplier teams like LG Electronics, Magna and Valeo and coordinated the corrective actions. I've also led a distributed 14-person validation team, which taught me to keep competing priorities moving and to write things down so the process survives me. Being the founding member of a quality function &mdash; defining the process instead of inheriting it &mdash; is exactly the part of this role that appeals to me.",
            "I'd be glad to talk about how I can help Kodiak build repeatable, data-driven quality processes as the team grows. Thank you for your time.",
        ],
    ),
    "chargepoint": dict(
        folder="ChargePoint_Staff_Electrical_Systems_Design_Engineer_8818017002_2026-10-13",
        summary=(
            "Electrical and electronic systems integration and validation engineer with 9+ years across automotive programs, "
            "including 5.5 years at Ford and 3.5 years of HIL validation with General Motors. I own systems-level integration and "
            "validation from requirements through release: defining interfaces between subsystems, reviewing architecture and "
            "design documents (HLD reviews, POC validation), building and bringing up test benches and vehicle test setups, "
            "developing and executing test plans for functional, regression, durability and stability behaviour, and diagnosing "
            "hardware-software issues hands-on with oscilloscopes, digital multimeters and data-acquisition equipment. Strong on "
            "failure analysis (FTA, RCA, 5-Why), on cross-disciplinary work with hardware, firmware, thermal, test and quality "
            "teams, and on documenting design and test decisions so a program can be audited and repeated."
        ),
        skills=[
            ("Systems Integration &amp; Interfaces", "System-Level Integration &amp; Validation &bull; Subsystem Boundary &amp; Interface Definition &bull; Requirements Analysis &amp; Traceability &bull; Architecture / HLD Review &amp; POC Validation &bull; Cross-Disciplinary Requirement Alignment"),
            ("Test Plans, Validation &amp; Reliability", "Test-Plan Development &amp; Execution &bull; Functional, Regression, Stability &amp; Durability Testing &bull; Pass/Fail Criteria Definition &bull; Bench &amp; Vehicle Bring-Up &bull; Defect Triage &amp; Corrective-Action Verification"),
            ("Lab, Measurement &amp; Diagnostics", "Oscilloscopes &bull; Digital Multimeters &bull; Data-Acquisition (DAQ) Boards &amp; Microcontrollers &bull; Signal Monitoring &amp; System-Response Analysis &bull; Failure Reproduction &amp; Characterization"),
            ("Failure Analysis &amp; Quality", "Fault Tree Analysis (FTA) &bull; Root-Cause Analysis &bull; PRA &bull; Fishbone &amp; 5-Why &bull; ISO 26262 Functional-Safety Awareness &bull; Quality Metrics &amp; Defect-Trend Reporting"),
            ("Networks &amp; Embedded", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; UDS &amp; DoIP &bull; QNX &amp; Android AOSP Multi-OS Embedded Systems &bull; CANoe/CANalyzer, Vehicle Spy, ValueCAN3/4"),
            ("Tools &amp; Delivery", "Python Automation (OOP) &bull; MATLAB/Simulink &bull; LabVIEW &bull; Danlaw Mx-Suite / MxVDev &bull; Vector VN-1630 &bull; JIRA, JAMA, IBM DOORS, Confluence &bull; Agile / Scrum &bull; Distributed Team Leadership (14+)"),
        ],
        project_order=["gm_hil", "fnv3", "fnv2", "fnv4", "pisquare"],
        cover_company="ChargePoint",
        cover_addr="Campbell, California",
        cover_paras=[
            "I'm writing to apply for the Staff Electrical Systems Design Engineer role on the DC fast charging team at ChargePoint. I've spent nine years on the validation and integration side of vehicle electrical systems, and I'd like to bring that systems-level view to work that puts more energy on the road rather than in a tailpipe.",
            "At Ford I own component-, system- and vehicle-level integration and validation across five vehicle programs. That means defining what has to be true at each subsystem boundary, reviewing architecture and design information with the architects and developers before we commit to it, and then building the bench or vehicle setup that proves it. I develop and run test plans for functional, regression, stability and durability behaviour, define the pass/fail criteria with the design teams, and when something fails I reproduce it and dig in with an oscilloscope or a multimeter until the root cause is nailed down. Fault Tree Analysis and structured RCA (PRA, Fishbone, 5-Why) are part of my normal week, and I keep ISO 26262 functional-safety thinking in the back of my head while doing it.",
            "Before Ford I spent three and a half years at Danlaw building HIL benches for GM's Global A and Global B platforms &mdash; configuring subsystem simulation models in Mx-Suite/MxVDev and integrating them with Vector VN-1630 interfaces so simulated and physical ECUs could talk over CAN/CAN-FD. Those benches had to be electrically sound, safe and repeatable before any test ran on them, and debugging across the electrical, mechanical and software layers at once became second nature. That work also taught me to write things down: interface definitions, test procedures, results and known issues, because a system nobody else can bring up is a liability.",
            "I'd welcome the chance to talk about how my integration and validation background could support ChargePoint's fast charging programs. Thank you for your consideration.",
        ],
    ),
    "geotab": dict(
        folder="Geotab_Senior_Field_Hardware_Engineer_5427604008_2026-10-13",
        summary=(
            "Vehicle systems validation engineer with 9+ years working on real vehicles and benches, including 5.5 years at Ford "
            "across five vehicle programs and 3.5 years of HIL validation with General Motors. Comfortable being hands-on with "
            "vehicle electrical and communication systems: diagnosing integration and communication faults on production vehicles, "
            "monitoring CAN/CAN-FD traffic with diagnostic tools, capturing data with oscilloscopes, digital multimeters and DAQ "
            "equipment, reproducing failures under known conditions and driving root cause to a documented fix. I plan and run "
            "vehicle-level test campaigns, collect and review test data for completeness and quality, write the installation, "
            "diagnostic and test procedures other engineers use, and report technical status and risk to leadership. I've led a "
            "distributed 14-person team and mentored engineers through hands-on guidance and review of their documentation."
        ),
        skills=[
            ("Vehicle-Level Testing &amp; Diagnostics", "Vehicle-Level Validation on Production Vehicles &bull; On-Board Diagnostics &amp; Fault Reproduction &bull; CAN / CAN-FD / LIN / Automotive Ethernet Analysis &bull; System Behaviour &amp; Signal Monitoring &bull; Root-Cause Analysis"),
            ("Measurement &amp; Data Collection", "Data Acquisition (DAQ) Boards &amp; Microcontrollers &bull; Oscilloscopes &amp; Digital Multimeters &bull; Sensor / Signal Capture &bull; Controlled Test Scenarios &amp; Test-Data Review &bull; ValueCAN3/4, RadMoon, Rad-Galaxy, Vehicle Spy, CANoe/CANalyzer"),
            ("Test Planning &amp; Execution", "Test-Campaign Planning &bull; Requirements-Based Test Cases (~3,100 authored in one program) &bull; Functional, Regression &amp; Stability Testing &bull; Repeatable Test Procedures &bull; Defect Tracking to Closure"),
            ("Documentation &amp; Reporting", "Installation, Diagnostic &amp; Test Procedures &bull; Test Plans &amp; Reports &bull; Defect &amp; Trend Analysis &bull; Status, Risk &amp; Recommendation Reporting to Leadership &bull; JIRA, Confluence, JAMA, IBM DOORS, TestRail"),
            ("Collaboration &amp; Coaching", "Cross-Functional Work with Feature Owners, Architects, Developers &amp; Suppliers &bull; Distributed Team Leadership (14+) &bull; Mentoring &amp; Knowledge Sharing &bull; Agile / Scrum"),
            ("Technical Foundations", "Embedded &amp; Multi-OS Systems (QNX, Android AOSP) &bull; ISO 26262 Functional-Safety Awareness &bull; ADAS Perception Sensors Overview (Camera, Radar, LiDAR) &bull; Python Automation (OOP) &bull; MATLAB/Simulink, LabVIEW"),
        ],
        project_order=["fnv2", "fnv3", "pisquare", "fnv4", "gm_hil"],
        cover_company="Geotab",
        cover_addr="Remote &mdash; United States",
        cover_paras=[
            "I'd like to apply for the Senior Field Hardware Engineer role supporting Geotab Video. My nine years have been spent testing vehicle systems where they actually live &mdash; on benches, but mostly on real vehicles &mdash; and the part of this job about walking up to a vehicle, working out what is wrong and getting it documented properly is very familiar ground.",
            "At Ford I run component-, system- and vehicle-level validation across five vehicle programs. A lot of that is hands-on: monitoring CAN and CAN-FD traffic with ValueCAN4 and RadMoon, capturing signals and system responses with data-acquisition equipment, an oscilloscope or a multimeter, and reproducing a fault under known conditions before I touch it. When a defect appears I characterize it, chase the root cause down with structured analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) and stay with it until the corrective action is validated &mdash; then track the trend and report it to the feature owners, architects and program leadership. I write the test procedures and reports other engineers use, because undocumented findings disappear as soon as the person who found them changes projects.",
            "I've also led a distributed 14-person validation team, which is where I got comfortable prioritizing several customer-impacting problems at once, keeping remote stakeholders informed, and coaching less-experienced engineers through hands-on guidance and review of their work. Before Ford I spent three and a half years at Danlaw building HIL benches for GM's Global A and Global B platforms, debugging integration failures together with OEM and supplier teams like LG Electronics, Magna and Valeo. Working with telematics and camera-based systems that feed AI models is a step I'd take gladly.",
            "Thank you for your time &mdash; I'd welcome the chance to talk about how I could support Geotab's field and pilot programs.",
        ],
    ),
    "scout": dict(
        folder="Scout_Motors_ADAS_DRE_Sensors_5262135007_2026-10-13",
        summary=(
            "Automotive systems validation and integration engineer with 9+ years, including 5.5 years at Ford across five Ford and "
            "Lincoln vehicle programs and 3.5 years of HIL validation with General Motors. I validate ADAS-related and connected "
            "features at component, system and vehicle level: planning and executing system-level tests, capturing and analyzing "
            "real-world vehicle data, evaluating behaviour against requirements and regulatory expectations, and tracking defects "
            "and integration issues through to closure. Working knowledge of ADAS/AD concepts and perception sensors (camera, "
            "radar, LiDAR), CAN/CAN-FD/Automotive Ethernet diagnostics with CANoe/CANalyzer and Vehicle Spy, and ISO 26262 "
            "functional-safety awareness. Based in Farmington Hills, MI, and used to close daily collaboration with electrical, "
            "software, validation and supplier teams."
        ),
        skills=[
            ("ADAS / AD &amp; Sensors", "ADAS/AD Systems Validation &amp; Integration (developing) &bull; ADAS Perception Sensors Overview (Camera, Radar, LiDAR) &bull; Sensor / Signal Monitoring &amp; Data Acquisition &bull; ROS / ROS 2, SLAM, Localization &amp; Sensor-Fusion Concepts (developing)"),
            ("System-Level Test &amp; Validation", "System-Level Test Planning &amp; Execution &bull; Component-, System- &amp; Vehicle-Level Validation &bull; Real-World / In-Vehicle Testing &amp; Data Analysis &bull; Requirements-Based Test Cases (~3,100 in one program) &bull; Performance Verification Against Requirements"),
            ("Issue Resolution", "Failure Reproduction &amp; Characterization &bull; Defect Triage &amp; Issue Tracking to Closure &bull; Root-Cause Analysis (PRA, RCA, FTA, Fishbone, 5-Why) &bull; Corrective-Action Validation with Design &amp; Supplier Teams &bull; Status &amp; Risk Reporting"),
            ("Standards &amp; Networks", "ISO 26262 Functional-Safety Awareness &bull; CAN / CAN-FD / LIN / Automotive Ethernet &bull; UDS &amp; DoIP &bull; CANoe / CANalyzer, Vehicle Spy, ValueCAN3/4, RadMoon, Vector VN-1630"),
            ("Measurement &amp; Data", "Digital Multimeter, Oscilloscopes, DAQ Boards, Microcontrollers &bull; Signal Capture &amp; System-Response Analysis &bull; Test-Bench &amp; Vehicle Test Setup &bull; Python Data Analysis &amp; Automation (OOP)"),
            ("Delivery &amp; Tools", "Cross-Functional Collaboration (Electrical, Software, Validation, Suppliers) &bull; Distributed Team Leadership (14+) &bull; Agile / Scrum &bull; JIRA, JAMA, IBM DOORS, Confluence, TestRail &bull; MATLAB/Simulink, LabVIEW, Mx-Suite"),
        ],
        project_order=["fnv3", "fnv2", "pisquare", "fnv4", "gm_hil"],
        cover_company="Scout Motors",
        cover_addr="Novi, Michigan",
        cover_paras=[
            "I'm applying for the ADAS DRE - Sensors role in Novi. I'm local &mdash; I live in Farmington Hills and have spent my career in this part of Michigan &mdash; and the mix of sensor-system validation, cross-functional coordination and issue ownership in the posting lines up well with how I work.",
            "At Ford I run component-, system- and vehicle-level validation across five Ford and Lincoln vehicle programs, including ADAS-related and connected features. In practice that means planning system-level tests, running them on benches and on production vehicles, capturing and analyzing real-world vehicle data, and judging behavior against the requirements and the standards the program has to meet. When a test fails I reproduce it, characterize the failure and work the root cause down with structured analysis &mdash; PRA, RCA, Fault Tree, Fishbone, 5-Why &mdash; then track the issue and its corrective action until it's genuinely closed. I keep ISO 26262 functional-safety thinking in mind throughout, and I work daily with electrical, software, validation and supplier teams rather than handing problems over a wall.",
            "My sensor exposure is real but at the system level rather than as a hardware owner: I work with perception-sensor concepts (camera, radar, LiDAR), monitor CAN/CAN-FD and Automotive Ethernet traffic with CANoe, CANalyzer and Vehicle Spy, and I'm currently building working knowledge of ROS/ROS 2, localization and sensor-fusion concepts. Before Ford I spent three and a half years at Danlaw on HIL benches for GM's Global A and Global B platforms, which is where I got comfortable debugging hardware, software and electrical issues together and coordinating fixes across OEM and supplier teams like LG Electronics, Magna and Valeo. I'd be glad to grow into full hardware release ownership under Scout's process.",
            "Thank you for your time &mdash; I'd welcome the chance to talk about the camera system work at Scout.",
        ],
    ),
    "gm_hil": dict(
        folder="General_Motors_Senior_System_Subsystem_HIL_Simulation_Integration_Engineer_JR-202620621_2026-10-14",
        summary=(
            "HIL and systems validation engineer with 9+ years in automotive, including 3.5 years building and running HIL "
            "benches for General Motors' Global A and Global B platforms and 5.5 years of component-, system- and vehicle-level "
            "validation at Ford. I build and bring up test benches end to end &mdash; wiring, loads, instrumentation, ECU hardware "
            "and models &mdash; write the real-time test configurations, and automate the tests so anyone can repeat them. Hands-on "
            "with MATLAB/Simulink-based test setups, Danlaw Mx-Suite/MxVDev, Vector VN-1630, CAN/CAN-FD with DBC/ARXML signal "
            "configuration, and instrumentation and simulation of ECU sensors and actuators. Strong at working out why a bench or "
            "a vehicle doesn't behave the way it should, running that down to root cause, and documenting bench and test "
            "requirements so the lab can hand the setup to the next engineer."
        ),
        skills=[
            ("HIL / SIL Validation", "Test-Bench Design, Build &amp; Bring-Up &bull; Real-Time HIL Simulation Models &bull; Plant-Model &amp; ECU Integration &bull; Model-Based &amp; Simulation-Based Testing &bull; Danlaw Mx-Suite / MxVDev &bull; Vector VN-1630"),
            ("Bench, Instrumentation &amp; Actuation", "Bench Wiring, Loads &amp; Instrumentation &bull; Simulation &amp; Instrumentation of ECU Sensors and Actuators &bull; Data-Acquisition (DAQ) Boards &amp; Signal Capture &bull; Digital Multimeters, Oscilloscopes, Microcontrollers &bull; Bench &amp; Test-Property Requirements Definition &bull; Lab User Training &amp; Support"),
            ("Test Automation &amp; Scripting", "Python Test Automation (OOP) &bull; Automated Regression &amp; Stability Runs &bull; Reusable Slash-Based &amp; Data-Driven Test Frameworks &bull; Efficiency &amp; Process Improvement &bull; MATLAB/Simulink, NI LabVIEW"),
            ("Systems &amp; Electrical Integration", "System- &amp; Subsystem-Level Integration &amp; Verification &bull; Electrical Design Integration and Verification &bull; Propulsion / Electrification, Chassis, Active Safety &amp; Body Controls Domains &bull; Hardware/Software Integration &bull; Requirements Analysis &amp; Traceability"),
            ("Vehicle Networks &amp; Diagnostics", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; DBC / ARXML Signal Configuration &bull; UDS &amp; DoIP &bull; CANoe / CANalyzer, Vehicle Spy, ValueCAN3/4, RadMoon"),
            ("Failure Analysis &amp; Quality", "Failure Reproduction &amp; Characterization &bull; Root-Cause Analysis (PRA/RCA, FTA, Fishbone, 5-Why) &bull; Defect Triage &amp; Trend Analysis &bull; Corrective-Action Verification with OEM &amp; Supplier Teams &bull; ISO 26262 Functional-Safety Awareness"),
            ("Delivery &amp; Collaboration", "OEM&ndash;Supplier Collaboration (LG Electronics, Magna, Valeo) &bull; Cross-Functional Work with System Architects, Developers &amp; Suppliers &bull; Distributed Team Leadership (14+) &bull; Agile / Scrum &bull; JIRA, JAMA, IBM DOORS, Confluence, Git"),
        ],
        project_order=["gm_hil", "fnv3", "fnv2", "fnv4", "pisquare"],
        cover_company="General Motors",
        cover_addr="Warren, Michigan",
        cover_paras=[
            "I'd like to apply for the Senior System &amp; Subsystem HIL Simulation Integration Engineer role at the Global Technical Center in Warren. I got my start in HIL benches almost nine years ago, and the work in this posting &mdash; building the bench, wiring the loads and instrumentation, integrating ECU hardware and models, then automating the tests &mdash; is what I've been doing on and off ever since.",
            "From 2017 to 2021 I worked on HIL benches for GM's Global A and Global B programs at Danlaw in Novi. I built and configured subsystem simulation models in Mx-Suite/MxVDev and integrated them with Vector VN-1630 interfaces so the simulation could talk to physical ECUs over CAN and CAN-FD, including DBC and ARXML signal configuration, regression runs and ECU response analysis. A lot of that job was figuring out why a bench didn't behave the way the model said it should &mdash; sometimes the wiring, sometimes a load, sometimes the model &mdash; and then fixing it with the OEM and supplier teams (LG Electronics, Magna and Valeo). I also wrote the reusable automation and monitoring pieces so a test could be re-run by someone else the next morning.",
            "Since 2021 I've been at Ford as a validation lead on benches and in vehicles across five Ford and Lincoln programs: configuring component, mini and full benches and the instrumentation on them, monitoring CAN/CAN-FD traffic with ValueCAN4 and RadMoon, and writing Python automation for functional, regression and stability testing. I authored roughly 3,100 functional and system test cases for one program and review high-level designs with system architects before testing starts. Day to day it's the same loop this role describes: something doesn't behave, reproduce it, characterize it, then run it down with structured analysis until the corrective action is verified.",
            "One honest note: my model work has been in Danlaw Mx-Suite/MxVDev and MATLAB/Simulink test environments rather than CarSim, VeDyna or ASM-VD vehicle-dynamics plant models, and I'd be learning the specifics of your lab tooling. What I bring is the bench build-and-bring-up side and the discipline around repeatability, documentation and handover. I'd welcome the chance to talk about the lab team at Estes &mdash; thank you for your time.",
        ],
    ),
    "zoox_seating": dict(
        folder="Zoox_Seating_and_Passive_Safety_HW_Validation_Engineer_04ccd0b8_2026-10-14",
        summary=(
            "Validation engineer with 9+ years owning validation from requirements through sign-off on automotive programs, "
            "including 5.5 years at Ford across five Ford and Lincoln vehicle programs. I develop and manage test plans, define "
            "the failure modes worth testing, choose the test assets, sensors and data-acquisition equipment that produce data I "
            "trust, analyze the results and report them, and stay on root cause until the corrective action is verified. I have "
            "authored about 3,100 requirements-based test cases in a single program, run internal and supplier-led validation, "
            "and worked daily with design, software and supplier engineers rather than handing problems over a wall. M.S. in "
            "Mechanical Engineering; hands-on with DAQ boards, sensors, oscilloscopes, digital multimeters, CAN/CAN-FD analysis "
            "and Python automation."
        ),
        skills=[
            ("Validation Planning &amp; Execution", "Validation Plans from Requirements to Sign-Off &bull; Failure-Mode Coverage Definition &bull; Test-Asset, Sensor &amp; Instrumentation Selection &bull; Mechanical, Electrical &amp; Environmental Test Exposure &bull; Validation Schedule &amp; Critical-Path Management"),
            ("Test Data &amp; Reporting", "Data Acquisition (DAQ) Boards &amp; Sensors &bull; Signal Capture &amp; System-Response Analysis &bull; Review of Test Data for Completeness &amp; Quality &bull; Clear Test-Result &amp; Failure Reporting &bull; Defect-Trend &amp; Quality-Metric Reporting"),
            ("Root Cause &amp; Corrective Action", "Failure Reproduction &amp; Characterization &bull; PRA, RCA, Fault Tree Analysis (FTA), Fishbone, 5-Why &bull; Root-Cause Support through Development, Validation &amp; Deployment &bull; Corrective-Action Verification with Design &amp; Supplier Teams"),
            ("Requirements &amp; Traceability", "Requirements Analysis, Traceability &amp; Management &bull; ~3,100 Requirements-Based Test Cases Authored in One Program &bull; Requirement Review with Design Engineers &bull; JAMA, IBM DOORS, JIRA, Confluence, TestRail (transferable to Polarion)"),
            ("Test Environments &amp; Measurement", "Component, Mini &amp; Full Test-Bench Configuration &amp; Bring-Up &bull; Vehicle-Level Validation on Production Vehicles &bull; Digital Multimeter, Oscilloscopes, DAQ Boards &bull; CAN / CAN-FD / LIN / Automotive Ethernet &bull; Python Data Analysis &amp; Automation (OOP)"),
            ("Collaboration &amp; Delivery", "Internal &amp; Supplier-Led Validation (LG Electronics, Magna, Valeo) &bull; Cross-Functional Work with Design, Software &amp; Supplier Engineers &bull; Distributed Team Leadership (14+) &bull; ISO 26262 Functional-Safety Awareness &bull; Agile / Scrum"),
        ],
        project_order=["fnv3", "fnv2", "fnv4", "gm_hil", "pisquare"],
        cover_company="Zoox",
        cover_addr="Foster City, California",
        cover_paras=[
            "I'm applying for the Seating and Passive Safety HW Validation Engineer role in Foster City. I'll be straight with you about the domain: my nine years of validation have been in vehicle electronics and embedded systems &mdash; infotainment, connected features, HIL benches &mdash; not seats, restraints or airbags. What I do bring is the validation discipline the role is built around: owning a plan from requirements to sign-off, deciding what failure modes are worth testing, making sure the test assets and instrumentation give me data I can defend, and staying on root cause until the fix is verified.",
            "At Ford I own component-, system- and vehicle-level validation across five Ford and Lincoln vehicle programs. That means writing test plans from requirements, reviewing them with the design and software engineers so the requirements are actually testable before hardware shows up, and then planning the assets I need &mdash; benches, vehicles, instrumentation &mdash; around the program's critical path. I authored about 3,100 functional and system-level test cases for one program with traceability back to the requirement, and I've managed supplier-led validation with teams at LG Electronics, Magna and Valeo, which is the same coordination problem as scheduling outside labs. When something fails I reproduce it, characterize the failure, and work it down with structured analysis &mdash; PRA, RCA, Fault Tree, Fishbone, 5-Why &mdash; then report results, defect trends and quality metrics to the program.",
            "The honest gaps: I haven't run DFMEAs myself, I haven't worked to FMVSS 207/208 or the crash-sled standards, and I haven't designed fixtures in CATIA. I've spent nine years inside requirements and validation processes in a different commodity, my M.S. is in Mechanical Engineering, and I'd expect to learn your standards and methods quickly &mdash; the measurement and instrumentation side (selecting sensors and data-acquisition hardware, and being strict about data quality before anything gets reported) transfers directly.",
            "I'd welcome the chance to talk about how a validation generalist could support the seating and passive safety work at Zoox. Thank you for your time.",
        ],
    ),
    "bosch_hw": dict(
        folder="Bosch_Senior_Hardware_Engineer_Plymouth_744000155078145_2026-10-14",
        summary=(
            "Automotive electronics validation and integration engineer with 9+ years across Ford and General Motors programs. "
            "I turn customer and program requirements into verification and validation plans with traceability back to the "
            "requirement, build and debug the bench or vehicle setup that proves them, and drive failures to root cause and "
            "verified corrective action. Hands-on at the electrical level with oscilloscopes, digital multimeters, DAQ boards and "
            "microcontrollers, and on vehicle networks (CAN/CAN-FD/LIN, Automotive Ethernet, UDS/DoIP). Comfortable in the areas "
            "around hardware design: requirements elicitation and review with OEM customers, verification and validation planning, "
            "bench-level debugging of validation and vehicle issues, design documentation and technical risk tracking through to "
            "release readiness."
        ),
        skills=[
            ("Verification &amp; Validation", "Hardware/Software Verification &amp; Validation Planning &bull; Requirements-to-Test Traceability &bull; Functional, Regression, Stability &amp; Durability Testing &bull; Pass/Fail Criteria Definition &bull; Validation Results &amp; Reporting"),
            ("Bench &amp; Vehicle Debugging", "Bench-Level Debugging &amp; Troubleshooting of Validation and Vehicle Issues &bull; Test-Bench Configuration &amp; Bring-Up &bull; Vehicle-Level Validation on Production Vehicles &bull; Oscilloscopes, Digital Multimeters, DAQ Boards, Microcontrollers &bull; Failure Reproduction &amp; Characterization"),
            ("Requirements &amp; Documentation", "Functional, Electrical &amp; Environmental Requirements Analysis &bull; Design-Review Participation (HLD Reviews, POC Validation) &bull; Technical Documentation &amp; Procedures &bull; Change &amp; Defect Tracking through to Release &bull; JIRA, JAMA, IBM DOORS, Confluence, TestRail"),
            ("Root Cause &amp; Corrective Action", "PRA &bull; RCA &bull; Fault Tree Analysis (FTA) &bull; Fishbone &amp; 5-Why &bull; Corrective-Action Verification with Design &amp; Supplier Teams &bull; Quality Metrics &amp; Defect-Trend Analysis"),
            ("Embedded &amp; Networks", "Multi-OS Embedded Systems (QNX, Android AOSP) &bull; CAN / CAN-FD / LIN / Automotive Ethernet &bull; UDS &amp; DoIP &bull; DBC / ARXML Signal Configuration &bull; CANoe / CANalyzer, Vehicle Spy, ValueCAN3/4, Vector VN-1630"),
            ("Tools &amp; Collaboration", "Python Automation (OOP) &bull; MATLAB/Simulink &bull; NI LabVIEW &bull; Danlaw Mx-Suite / MxVDev &bull; OEM&ndash;Supplier Collaboration (LG Electronics, Magna, Valeo) &bull; Distributed Team Leadership (14+) &bull; Agile / Scrum"),
        ],
        project_order=["fnv2", "fnv3", "gm_hil", "fnv4", "pisquare"],
        cover_company="Robert Bosch LLC",
        cover_addr="Plymouth, Michigan",
        cover_paras=[
            "I'd like to apply for the Senior Hardware Engineer role in Plymouth. I'll be direct about the shape of my experience: my career has been on the verification, validation and systems integration side of automotive electronics rather than in design ownership, so schematic capture and PCB layout are not things I have owned. The rest of what the posting describes &mdash; working with OEM customers on requirements, verification and validation planning with traceability, bench-level debugging, root-cause analysis, documentation and design reviews &mdash; is what I've done for nine years, mostly on infotainment, connectivity and connected-vehicle electronics, which is exactly the product area this team builds.",
            "At Ford I own component-, system- and vehicle-level validation across five Ford and Lincoln vehicle programs, including the SYNC 4 infotainment platform, where I test on benches and in production vehicles, review high-level designs and POCs with system architects before testing, and keep traceability from each requirement to its test and result &mdash; about 3,100 functional and system test cases in one program. When a validation, manufacturing or vehicle issue shows up, I reproduce it and debug it at the bench with an oscilloscope, a multimeter or data-acquisition equipment, then work it to root cause with structured analysis (FTA, RCA, Fishbone, 5-Why) and follow the corrective action until it's verified. I write the requirements, test procedures and issue documentation other engineers work from, and I work with suppliers like LG Electronics, Magna and Valeo when the problem crosses company lines.",
            "Before Ford I spent three and a half years at Danlaw building HIL benches for GM's Global A and Global B platforms: subsystem simulation models in Mx-Suite/MxVDev, Vector VN-1630 interfaces, CAN/CAN-FD communication with physical ECUs and DBC/ARXML signal configuration. That's where I learned to debug electrical, software and model problems together, and where I got used to defining bench requirements clearly enough that another engineer could pick the setup up.",
            "I'd be moving into design ownership for the first time and would expect to ramp on schematic capture, layout guidance and DFMEA practice. What I'd bring on day one is the verification, validation and bench-debug side of the product life cycle, plus a habit of documenting decisions so a program can be audited. I'd welcome the chance to talk about where that fits on your team. Thank you for your time.",
        ],
    ),
    "zoox_sdet": dict(
        folder="Zoox_Software_Development_Engineer_in_Test_d3a7605d_2026-10-14",
        summary=(
            "Software validation engineer with 9+ years in automotive, including 3.5 years building and running HIL benches for "
            "General Motors' Global A and Global B platforms and 5.5 years of component-, system- and vehicle-level validation at "
            "Ford. I work where release quality is decided: configuring HIL/SIL benches with Danlaw Mx-Suite/MxVDev and Vector "
            "VN-1630, writing Python automation and reusable test frameworks for functional, regression and stability suites, running "
            "those suites through CI and artifact tooling (Jenkins, JFrog, Nexus, Git), and leading root-cause analysis when a build "
            "fails. I own requirements-to-test traceability &mdash; about 3,100 functional and system test cases in one program &mdash; "
            "identify gaps between requirements and test implementation, and summarize failure impact and defect trends for feature "
            "owners, system architects and program leadership. I use AI-assisted coding (GitHub Copilot, OpenCode) daily for test "
            "generation and tooling, and I am building toward ADAS/AD validation &mdash; ROS/ROS 2, SLAM, localization and "
            "sensor-fusion concepts &mdash; to bring this validation background to autonomous-vehicle software."
        ),
        skills=[
            ("HIL / SIL Test &amp; Release Validation", "Hardware-in-the-Loop &amp; Software-in-the-Loop Validation &bull; Real-Time Simulation &amp; ECU Interaction (Danlaw Mx-Suite / MxVDev, Vector VN-1630) &bull; Test Plans, Test-Case Design &amp; Execution &bull; Functional, Regression &amp; Stability Suites &bull; Release Readiness &amp; Sign-Off Support &bull; Pass/Fail Criteria Definition"),
            ("Test Automation &amp; Frameworks", "Python Scripting &amp; Automation (OOP) &bull; Reusable Automation Templates (Slash-Based &amp; Data-Driven Testing) &bull; Custom Test &amp; Monitoring Solutions &bull; CI &amp; Build Tooling (Jenkins, JFrog, Nexus, Git/GitBash) &bull; AI-Assisted Test Generation (GitHub Copilot, OpenCode)"),
            ("Root Cause &amp; Failure Analysis", "Root Cause Analysis of System-Level Failures &bull; PRA, RCA, Fault Tree Analysis (FTA), Fishbone, 5-Why &bull; Failure Reproduction &amp; Characterization &bull; Defect Triage, Quality Metrics &amp; Defect-Trend Reporting &bull; Corrective-Action Verification"),
            ("Requirements, Safety &amp; Traceability", "Requirements Analysis &amp; Traceability (JAMA, IBM DOORS) &bull; Requirements-to-Test Gap Analysis &bull; Traceability Matrix Authoring (~3,100 Test Cases) &bull; HLD Review &amp; POC Validation &bull; ISO 26262 Functional Safety Awareness"),
            ("Embedded Systems &amp; Networks", "Multi-OS Embedded Systems (QNX, Android AOSP) &bull; CAN / CAN-FD / LIN / Automotive Ethernet &bull; UDS &amp; DoIP &bull; DBC / ARXML Signal Configuration &bull; Signal Monitoring, Data Acquisition &amp; System-Response Analysis (ValueCAN4, RadMoon, CANoe/CANalyzer, Vehicle Spy) &bull; Electrical &amp; Electronic Systems: Bench Wiring, Signal-Level Debugging, Oscilloscopes, Digital Multimeters, DAQ Boards, Microcontrollers &bull; Field Failure Investigation on Production Vehicles"),
            ("Systems &amp; Collaboration", "ADAS / AD Concepts (ROS / ROS 2, SLAM, Localization, Sensor Fusion &mdash; developing) &bull; Distributed Team Leadership (14+) &bull; OEM&ndash;Supplier Collaboration (LG Electronics, Magna, Valeo) &bull; Technical Documentation (Confluence) &bull; Agile / Scrum"),
        ],
        project_order=["gm_hil", "fnv3", "fnv4", "fnv2", "pisquare"],
        cover_company="Zoox",
        cover_addr="Foster City, California",
        cover_paras=[
            "I'm applying for the Software Development Engineer in Test role on the Release Management team. I'll be straightforward about where I'm coming from: nine years of automotive validation rather than time inside an AV program. The core of the job &mdash; HIL/SIL test frameworks that help decide whether a release is safe to ship, Python automation built to last, and root-cause work when a system-level failure shows up &mdash; is what I've done every day for those nine years.",
            "At Ford I own component-, system- and vehicle-level validation across five vehicle programs. I build and maintain Python automation for functional, regression and stability suites, run them on benches and in production vehicles, and when something fails I reproduce it, work it to root cause with structured analysis (FTA, RCA, Fishbone, 5-Why) and write up the failure and its impact for feature owners, system architects and program leadership. I keep traceability from each requirement to its test and result &mdash; roughly 3,100 functional and system test cases in one program &mdash; and I've built AI-assisted workflows with GitHub Copilot and OpenCode that generate test coverage and traceability entries, which is close to the tooling this posting describes.",
            "Before Ford I spent three and a half years at Danlaw building HIL benches for GM's Global A and Global B platforms: subsystem simulation models in Mx-Suite/MxVDev, Vector VN-1630 interfaces, CAN/CAN-FD communication with physical ECUs, DBC/ARXML signal configuration and regression runs, plus the root-cause work when the bench and the ECU disagreed. I also led a distributed 14-person validation team, which is where I learned to summarize a complex failure clearly enough that someone else can act on it.",
            "Where I'd need to ramp is the part specific to an autonomous stack &mdash; real-time fault injection at your scale, the safety-critical monitors you clear, and Linux internals in a high-throughput real-time system. I'm studying ROS/ROS 2, SLAM, localization and sensor-fusion concepts to close the domain gap, and I'd bring the validation discipline, the automation habits and the documentation with me. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),
    "valeo_motors": dict(
        folder="Valeo_Platform_Module_Integrator_Motors_REQ2026082128_2026-10-14",
        summary=(
            "Systems integration and validation engineer with 9+ years in automotive, working at the boundary between OEM customers and "
            "supplier engineering teams. I validate that what was engineered meets the requirement: requirements analysis and "
            "traceability, compliance checks against agreed standards, bench/HIL and vehicle-level validation, change and defect "
            "tracking through to verified closure, and the technical documentation and training material that keeps a platform "
            "consistent across sites. My product experience is on the electrical and embedded side of vehicle programs, including "
            "electrified platforms (Mustang Mach-E, F-150 Lightning) and CAN/CAN-FD, UDS/DoIP and Automotive Ethernet communication. I "
            "have worked directly with suppliers including LG Electronics, Magna and Valeo on General Motors' Global A and Global B "
            "programs, lead distributed teams (14+), run cross-functional issue resolution and report risk and status to program "
            "leadership."
        ),
        skills=[
            ("Systems Integration &amp; Validation", "Component-, System- &amp; Vehicle-Level Integration &amp; Validation &bull; Bench &amp; HIL Test Environments (Danlaw Mx-Suite / MxVDev, Vector VN-1630) &bull; Pass/Fail Criteria Definition &bull; Regression &amp; Stability Testing &bull; Validation Results &amp; Reporting"),
            ("Requirements, Compliance &amp; Documentation", "Requirements Analysis &amp; Traceability (JAMA, IBM DOORS) &bull; Requirements-to-Test Coverage &amp; Traceability Matrices &bull; Compliance to Agreed Standards &amp; Specifications &bull; Technical Documentation &amp; Procedures (Confluence) &bull; ISO 26262 Functional Safety Awareness"),
            ("Change, Defect &amp; Risk Management", "Defect Triage &amp; Root Cause Analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) &bull; Change &amp; Defect Tracking through to Release &bull; Corrective-Action Verification with OEM &amp; Supplier Teams &bull; Risk &amp; Status Reporting to Program Leadership &bull; Agile / Scrum"),
            ("Program &amp; Customer Coordination", "OEM&ndash;Supplier Collaboration (LG Electronics, Magna, Valeo) &bull; Cross-Functional Issue Resolution &bull; Distributed Team Leadership (14+) &bull; Test-Case Authoring (~3,100) &bull; Process Standardization &amp; Team Training"),
            ("Electrified Vehicle Programs", "Vehicle-Level Validation on Electrified Platforms &mdash; EV (Electric Vehicle) Programs: Mustang Mach-E &amp; F-150 Lightning &bull; Electrical &amp; Signal Behavior Validation &bull; Diagnostic &amp; Communication Protocols (UDS, DoIP, CAN/CAN-FD, Automotive Ethernet) &bull; Multi-OS Embedded Systems (QNX, Android AOSP)"),
            ("Engineering Tools", "Python Automation (OOP) &bull; MATLAB/Simulink &bull; NI LabVIEW &bull; CANoe/CANalyzer, Vehicle Spy, ValueCAN4, RadMoon &bull; JIRA, Confluence, TestRail &bull; Git/GitBash"),
        ],
        project_order=["fnv2", "fnv3", "fnv4", "gm_hil", "pisquare"],
        cover_company="Valeo",
        cover_addr="Auburn Hills, Michigan",
        cover_paras=[
            "I'd like to apply for the Platform/Module Integrator (Motors) role in Auburn Hills. Let me be direct: my background is the validation and systems integration side of automotive electronics and software, not electrical machines or power-electronics design ownership. What I do have is nine years of keeping engineering honest about requirements and standards &mdash; and I've worked with Valeo's own engineering teams as a supplier on GM's Global A and Global B programs.",
            "At Ford I validate component-, system- and vehicle-level behaviour across five vehicle programs, including electrified platforms like the Mustang Mach-E and F-150 Lightning. Day to day that means checking that designs and changes meet the agreed requirements before we release them, keeping requirements-to-test traceability (about 3,100 test cases in one program), running bench, HIL and vehicle-level validation, and chasing every defect to a verified corrective action. When a change lands, I check it follows the right review path and that the traceability and technical documentation stay current.",
            "At Danlaw I built HIL benches for GM's Global A and Global B platforms &mdash; Mx-Suite/MxVDev models, Vector VN-1630 interfaces, CAN/CAN-FD with DBC/ARXML signal configuration &mdash; and ran the root-cause work across company lines with OEM and supplier teams including LG Electronics, Magna and Valeo. I also led a distributed 14-person validation team and standardized how we worked through written frameworks and training, because a platform only stays consistent if the people using it are trained on it.",
            "Where I'd need to ramp is the product knowledge this role is built on: alternators and starter motors across 12V and 48V, high-voltage motors and topologies like axial flux, and the power-module, capacitor and PCB side of high-voltage systems. That's real learning I'd expect to do with your PTMs and standard owners. What I'd bring from day one is the gatekeeper instinct &mdash; checking DR conclusions, compliance matrices and DSRs against platform standards, representing the platform in technical committees, and keeping documentation and training in shape. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),

    # ------------------------------------------------------------------ 2026-10-15 real-search queue
    "zoox_avvv": dict(
        folder="Zoox_Systems_Engineer_Autonomy_Verification_and_Validation_1d0b857f_2026-10-14",
        summary=(
            "Verification and validation systems engineer with 9+ years in automotive, including 3.5 years building and running "
            "HIL benches for General Motors' Global A and Global B platforms and 5.5 years of component-, system- and "
            "vehicle-level validation at Ford across five Ford and Lincoln vehicle programs. I write validation plans from "
            "requirements and stand behind them &mdash; defining what has to be true at the component, system and vehicle level, "
            "building or configuring the bench, vehicle and simulation setup that exercises it, reviewing verification and "
            "simulation results, and reporting findings with the evidence to back them up. I have authored roughly 3,100 "
            "requirements-based functional and system test cases in one program, kept traceability from requirement to result, "
            "and led root-cause analysis across hardware, software and supplier boundaries. Comfortable working cross-functionally "
            "with system architects, software teams and program leadership, and building toward autonomy &mdash; real-world and "
            "simulation-based V&amp;V methods that substantiate a safety case for autonomous driving."
        ),
        skills=[
            ("Verification &amp; Validation", "Validation Planning from Requirements to Sign-Off &bull; Verification &amp; Validation Methodology &bull; Requirements-Based Test Strategy &bull; Coverage Definition &amp; Gap Analysis &bull; Simulation &amp; Verification-Result Review &bull; Validation Reporting"),
            ("Autonomy / ADAS Systems", "ADAS / AV V&amp;V and Autonomy Concepts (developing) &bull; Perception-Sensor Concepts (Camera, Radar, LiDAR) &bull; Sensor / Signal Monitoring &amp; Data Acquisition &bull; System Behavior &amp; State-Transition Validation &bull; ROS / ROS 2 and Sensor-Fusion Concepts (developing)"),
            ("Real-World &amp; Virtual Testing", "Vehicle-Level Validation on Production Vehicles &bull; HIL / SIL / MIL Testing (Danlaw Mx-Suite, Vector VN-1630) &bull; Model-Based &amp; Simulation-Based Testing &bull; Bench &amp; Vehicle Test Setup &bull; Test-Case Authoring (~3,100 in one program)"),
            ("Requirements, Safety &amp; Traceability", "Requirements Analysis &amp; Traceability (JAMA, IBM DOORS) &bull; ISO 26262 Functional-Safety Awareness &bull; Risk-Based / Failure-Mode Validation &bull; Corrective-Action Verification &bull; HLD Review &amp; POC Validation"),
            ("Root Cause &amp; Failure Analysis", "PRA, RCA, Fault Tree Analysis (FTA), Fishbone, 5-Why &bull; Failure Reproduction &amp; Characterization &bull; Defect-Triage &amp; Trend Analysis &bull; Cross-Functional Issue Resolution"),
            ("Embedded Systems &amp; Networks", "Multi-OS Embedded Systems (QNX, Android AOSP) &bull; CAN / CAN-FD / LIN / Automotive Ethernet &bull; UDS &amp; DoIP &bull; CANoe / CANalyzer, Vehicle Spy, ValueCAN4, RadMoon"),
            ("Tools &amp; Collaboration", "Python Automation (OOP) &bull; MATLAB/Simulink &bull; NI LabVIEW &bull; Cross-Functional Work with System Architects, Software Teams &amp; Program Leadership &bull; Distributed Team Leadership (14+) &bull; JIRA, JAMA, IBM DOORS, Confluence &bull; Agile / Scrum"),
        ],
        project_order=["gm_hil", "fnv3", "fnv4", "fnv2", "pisquare"],
        cover_company="Zoox",
        cover_addr="Foster City, California",
        cover_paras=[
            "I'd like to apply for the Systems Engineer role on the Autonomy Verification and Validation team in Foster City. I'll be direct about the domain: my nine years are in automotive validation &mdash; infotainment, connected features and HIL benches &mdash; rather than inside an autonomous-driving program. What I bring is the part of the job I've done every day: turning requirements into a validation plan, deciding what has to be proven at each level, running the tests that prove it, and reporting the result honestly.",
            "At Ford I own component-, system- and vehicle-level validation across five Ford and Lincoln vehicle programs. I write validation plans from requirements, review them with system architects and software engineers so the requirements are testable before testing starts, and then plan the bench, vehicle and instrumentation I need to execute them. I authored about 3,100 functional and system test cases for one program, with traceability from each requirement to its result, and I review results against expected behaviour rather than just running to completion. When a system-level failure shows up I reproduce it, characterize it and work the root cause down with structured analysis &mdash; PRA, RCA, Fault Tree, Fishbone, 5-Why &mdash; then follow the corrective action until it's verified. I kept that up through QNX and Android AOS integration, where the interactions between host and guest operating systems made expected behaviour anything but obvious.",
            "Before Ford I spent three and a half years at Danlaw building and running HIL benches for GM's Global A and Global B platforms &mdash; Mx-Suite/MxVDev subsystem models and simulation, integrated with Vector VN-1630 interfaces so simulated and physical ECUs could exercise each other over CAN/CAN-FD. That's where I learned to treat simulation as evidence: when a virtual test and a real-world test disagree, that disagreement is usually the most useful thing you learn all week. I've worked across program, software and supplier teams (LG Electronics, Magna, Valeo) rather than handing problems over a wall, which is the part of a cross-functional V&amp;V role that doesn't worry me.",
            "Where I'd need to ramp is the AV-specific side &mdash; the safety-case and fail-operational methodology, real-time fault injection at autonomous scale, and reviewing verification and simulation results for an autonomy stack. I'm studying ROS/ROS 2, SLAM, localization and sensor-fusion concepts to close that gap, and I'd bring the validation discipline, the traceability habits and the documentation with me. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),
    "zoox_hwtest": dict(
        folder="Zoox_Hardware_Engineer_Test_Development_a90cfd71_2026-10-14",
        summary=(
            "Hands-on hardware and systems test engineer with 9+ years in automotive, including 5.5 years at Ford across five "
            "Ford and Lincoln vehicle programs and 3.5 years of HIL validation with General Motors. I build the test setup and "
            "then get trustworthy data out of it &mdash; configuring benches, wiring and instrumentation, selecting sensors and "
            "data-acquisition equipment, writing Python automation so tests run repeatably, executing functional and stress "
            "testing, and driving failures to root cause. I have run component-, system- and vehicle-level validation against "
            "requirements, authored roughly 3,100 requirements-based test cases in one program, and I use AI-assisted tooling "
            "(GitHub Copilot, OpenCode) to build and run tests faster. Comfortable owning a bench or lab setup end to end and "
            "handing it to the next engineer, with exposure to autonomous-vehicle and autonomy hardware programs."
        ),
        skills=[
            ("Test Setup &amp; Automation", "Test-Bench / Lab Setup, Design &amp; Bring-Up &bull; Wiring, Loads &amp; Instrumentation &bull; Python Test Automation (OOP) &bull; Automated Regression &amp; Stability Runs &bull; Reusable Slash-Based &amp; Data-Driven Frameworks &bull; AI-Assisted Tooling (GitHub Copilot, OpenCode)"),
            ("DV / PV &amp; Stress Testing", "Design Validation (DV) &amp; Production Validation (PV) Exposure &bull; Requirements-Based Qualification Testing &bull; Temperature, Power, Vibration &amp; Lifetime-Stress Test Setup &bull; Functional, Regression &amp; Durability Testing &bull; Pass/Fail Criteria Definition"),
            ("Instrumentation &amp; Data", "Sensors &amp; Data-Acquisition (DAQ) Boards &bull; Oscilloscopes, Digital Multimeters, Microcontrollers &bull; Signal Capture &amp; System-Response Analysis &bull; ValueCAN4, RadMoon, CANoe/CANalyzer, Vehicle Spy"),
            ("Failure Analysis &amp; Root Cause", "Failure Reproduction &amp; Characterization &bull; PRA, RCA, Fault Tree Analysis (FTA), Fishbone, 5-Why &bull; Defect Triage &amp; Corrective-Action Verification &bull; Cross-Functional Debugging with Hardware &amp; Software Teams"),
            ("Embedded, Electrical &amp; Electronic Systems", "ECU / Embedded Hardware Validation &bull; Electrical &amp; Electronic Systems &mdash; Bench Wiring &amp; Signal-Level Debugging &bull; Multi-OS Embedded Systems (QNX, Android AOSP) &bull; CAN / CAN-FD / LIN / Automotive Ethernet &bull; UDS &amp; DoIP &bull; DBC / ARXML Signal Configuration &bull; HIL (Danlaw Mx-Suite / MxVDev, Vector VN-1630)"),
            ("Tools &amp; Collaboration", "MATLAB/Simulink &bull; NI LabVIEW &bull; Git &bull; JIRA, JAMA, IBM DOORS, Confluence &bull; OEM&ndash;Supplier Collaboration (LG Electronics, Magna, Valeo) &bull; Distributed Team Leadership (14+) &bull; Agile / Scrum"),
        ],
        project_order=["fnv3", "gm_hil", "fnv2", "fnv4", "pisquare"],
        cover_company="Zoox",
        cover_addr="Foster City, California",
        cover_paras=[
            "I'd like to apply for the Hardware Engineer role on the Test Development team in Foster City. The part of the posting about being the hands-on engineer who actually gets testing done &mdash; building the setup, wiring it, running it, and then working out why something failed &mdash; is the half of validation I like best, and it's most of what I've done for nine years.",
            "At Ford I run component-, system- and vehicle-level validation across five Ford and Lincoln vehicle programs, on component benches, mini benches, partial and full test benches, and production vehicles. I configure the setup: the hardware, the wiring and instrumentation, the communication interfaces and the test configuration. I capture and analyze data from it &mdash; CAN and CAN-FD traffic with ValueCAN4 and RadMoon, signals and system responses with data-acquisition equipment, an oscilloscope or a multimeter &mdash; and I write and maintain Python automation so a test can be re-run the next morning and give the same answer. When a test fails I reproduce it, characterize the failure and chase the root cause with PRA, RCA, Fault Tree, Fishbone and 5-Why until we understand it. I authored about 3,100 functional and system test cases for one program, and I use GitHub Copilot and OpenCode to build test tooling faster, which is close to the automation your posting asks for.",
            "Before Ford I spent three and a half years at Danlaw building HIL benches for GM's Global A and Global B platforms &mdash; subsystem simulation models in Mx-Suite/MxVDev, integrated with Vector VN-1630 interfaces so simulation and physical ECUs could exercise each other over CAN/CAN-FD. A lot of that job was debugging the bench itself: a load, a wiring run, a model that didn't match the hardware. That's the same instinct the DV and PV work here needs, where the ECU team is depending on you to tell them whether the unit failed or the rig lied.",
            "One honest gap: I haven't owned a formal temperature, vibration or EMC qualification program end to end, and cold-weather qualification would be new to me. I have built and run the benches those programs sit on, and I'm strict about data quality before anything gets reported, so I'd expect to ramp on your methods and chambers quickly. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),
    "waymo_fieldq": dict(
        folder="Waymo_Staff_Field_Quality_Engineer_7964147_2026-10-12",
        summary=(
            "Validation and quality engineer with 9+ years in automotive, including 5.5 years at Ford across five Ford and "
            "Lincoln vehicle programs and 3.5 years of HIL validation with General Motors. My work is built around finding and "
            "fixing the cause of field and bench failures: reproducing and characterizing failures on production vehicles, "
            "leading structured root-cause analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why), tracking defect trends and quality "
            "metrics, and driving containment and corrective actions to verified closure with internal teams and suppliers "
            "including LG Electronics, Magna and Valeo. I define the validation coverage a fix needs to prove it worked, then "
            "confirm it holds, and I report trends and risk to program leadership. I analyze test and vehicle data in Python and "
            "have led a distributed 14-person validation team."
        ),
        skills=[
            ("Root Cause &amp; Corrective Action", "Cross-Functional Root Cause Analysis &bull; PRA, RCA, Fault Tree Analysis (FTA), Fishbone, 5-Why &bull; Failure Reproduction &amp; Characterization on Production Vehicles &bull; Containment &amp; Corrective-Action Verification &bull; Preventing Recurrence"),
            ("Quality &amp; Reliability", "Defect Triage &amp; Trend Analysis &bull; Quality-Metric Reporting &bull; Validation-Coverage Definition &bull; Reliability-Focused Test &amp; Validation &bull; Corrective-Action Effectiveness Verification"),
            ("Field Failure &amp; Fleet Data", "Field-Style Failure Investigation on Production Vehicles &bull; On-Board Diagnostics &amp; Fault Reproduction &bull; Data Acquisition &amp; System-Response Analysis &bull; Test / Fleet-Data Review &bull; Autonomy / Autonomous-Vehicle &amp; AV Domain Exposure (developing) &bull; Python Data Analysis"),
            ("Cross-Functional Leadership &amp; Supplier Quality", "OEM&ndash;Supplier Collaboration (LG Electronics, Magna, Valeo) &bull; Leading Cross-Functional Issue Resolution &bull; Distributed Team Leadership (14+) &bull; Status, Risk &amp; Recommendation Reporting to Leadership"),
            ("Test, Measurement &amp; Embedded", "Test-Bench / HIL Configuration (Danlaw Mx-Suite, Vector VN-1630) &bull; Embedded Systems (QNX, Android AOSP) &bull; Electrical &amp; Electronic Systems (Bench Wiring, Signal-Level Debugging) &bull; Oscilloscopes, Digital Multimeters, DAQ Boards &bull; CAN / CAN-FD / LIN / Automotive Ethernet &bull; CANoe/CANalyzer, Vehicle Spy, ValueCAN4, RadMoon"),
            ("Tools &amp; Methodologies", "Python (Data Analysis, Automation, OOP) &bull; MATLAB/Simulink &bull; JIRA, JAMA, IBM DOORS, Confluence, TestRail &bull; Git &bull; Agile / Scrum"),
        ],
        project_order=["fnv3", "fnv2", "gm_hil", "fnv4", "pisquare"],
        cover_company="Waymo",
        cover_addr="Mountain View, California",
        cover_paras=[
            "I'd like to apply for the Staff Field Quality Engineer role in Mountain View. Field quality is the part of validation that keeps score after launch, and my nine years have been spent on the loop this role describes: something fails in the field or on a vehicle, we reproduce and characterize it, we find the cause, we agree a fix, and then we prove the fix actually holds.",
            "At Ford I run component-, system- and vehicle-level validation across five Ford and Lincoln vehicle programs, and I lead the root-cause work when something fails on a bench or a production vehicle. That means reproducing the failure, characterizing it, and working it down with structured analysis &mdash; PRA, RCA, Fault Tree, Fishbone, 5-Why &mdash; then tracking the defect trend and the quality metrics and presenting them to feature owners, system architects and program leadership. I define what validation coverage a corrective action needs before we call it closed, and I stay on it until the behaviour is verified. I analyze the test and vehicle data in Python, and I've kept this up across QNX and Android AOS platforms, where a failure can sit at the boundary between two systems and two teams.",
            "Before Ford I spent three and a half years at Danlaw on HIL benches for GM's Global A and Global B platforms, where much of the root-cause work ran across company lines &mdash; I debugged integration failures with OEM and supplier teams like LG Electronics, Magna and Valeo and coordinated the containment and corrective actions. I've also led a distributed 14-person validation team, which is where I learned to keep several field-impacting problems moving at once and to write a finding down clearly enough that someone else can act on it. That documentation-and-feedback habit is the \"lessons learned improve the next design\" loop the posting is asking for.",
            "Honest gaps: I haven't formally run 8D, DMAIC, MSA, SPC or DOE programs, and my statistical tooling is Python rather than JMP or Tableau &mdash; I'd be learning those methods and tools as I go. What I bring from day one is the field-failure investigation, the cross-functional root-cause leadership, and the discipline of verifying a corrective action instead of assuming it worked. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),
    "magna_vipe": dict(
        folder="Magna_Vehicle_Integration_Project_Engineer_R00262327_2026-10-15",
        summary=(
            "Vehicle integration and validation engineer with 9+ years in automotive, including 5.5 years at Ford across five "
            "Ford and Lincoln vehicle programs and 3.5 years of HIL validation with General Motors. My day-to-day is component-, "
            "subsystem-, system- and vehicle-level validation: I take requirements and architectural specifications, work them into "
            "validation plans, test cases and coverage, then execute on benches and on production vehicles, analyze what the "
            "systems actually did, and drive failures to root cause with the people who own the design. I have maintained "
            "requirements traceability end to end (IBM DOORS, JAMA, RTM), authored roughly 3,100 requirements-based test cases in "
            "one program, and worked cross-functionally with OEM customers and supplier engineering teams including Magna, Valeo "
            "and LG Electronics &mdash; measuring system behaviour against customer requirements and specifications, and driving "
            "findings back to the customer and supplier owners. I report validation status, defect trends and quality metrics to "
            "program leadership and have led a distributed 14-person validation team."
        ),
        skills=[
            ("Vehicle Integration &amp; Validation", "Component-, Subsystem-, System- &amp; Vehicle-Level Validation &bull; Systems Integration &amp; V&amp;V &bull; Requirements-Based Validation Planning &amp; Test Strategies &bull; Validation Coverage Definition &amp; Gap Analysis &bull; Bench &amp; Vehicle-Level Testing &bull; Production-Release Support"),
            ("Requirements &amp; Traceability", "Requirements Management &amp; Traceability (IBM DOORS, JAMA) &bull; Requirements-to-Test-Case Traceability (RTM) &bull; Test-Case Authoring (~3,100 Functional &amp; System-Level Cases) &bull; HLD Review &amp; POC Validation &bull; Design / Technical &amp; Program Review Participation &bull; Requirements-to-Test-Strategy Translation"),
            ("Root Cause &amp; Quality", "PRA, RCA, Fault Tree Analysis (FTA), Fishbone, 5-Why &bull; Failure Reproduction &amp; Characterization &bull; Defect Triage &amp; Trend Analysis &bull; Quality-Metric Reporting to Program Leadership &bull; Corrective-Action Verification &bull; Cross-Functional Issue Resolution"),
            ("Embedded &amp; Electrical / Electronic Systems", "ECU &amp; Software Integration Validation &bull; Multi-OS Embedded Systems (QNX, Android AOSP) &bull; CAN / CAN-FD / LIN / Automotive Ethernet &bull; UDS &amp; DoIP &bull; DBC / ARXML Signal Configuration &bull; HIL (Danlaw Mx-Suite / MxVDev, Vector VN-1630)"),
            ("OEM&ndash;Supplier Collaboration &amp; Leadership", "OEM Customer Requirements &amp; Specifications &bull; OEM&ndash;Supplier Collaboration (including Magna, Valeo, LG Electronics) &bull; Cross-Functional Program Execution &bull; Distributed Team Leadership (14+) &bull; Technical Status, Risk &amp; Recommendation Reporting &bull; Supplier Issue Troubleshooting &amp; Corrective Actions"),
            ("Tools &amp; Automation", "Python Test Automation (OOP) &bull; Slash-Based &amp; Data-Driven Testing &bull; MATLAB/Simulink, NI LabVIEW &bull; AI-Assisted Tooling (GitHub Copilot, OpenCode) &bull; Git, JIRA, Confluence, TestRail &bull; Agile / Scrum"),
        ],
        project_order=["fnv3", "fnv2", "gm_hil", "fnv4", "pisquare"],
        cover_company="Magna Steyr (Magna International)",
        cover_addr="Troy, Michigan",
        cover_paras=[
            "I'd like to apply for the Vehicle Integration Project Engineer role in Troy. What pulled me toward this posting is the scope &mdash; complete vehicle programs, systems integrated and then proved out at the vehicle level, with the OEM and the supply base in the same room. That is the part of the job I have actually been doing for nine years, just from the validation and integration side rather than the design side.",
            "At Ford I run component-, subsystem-, system- and vehicle-level validation across five Ford and Lincoln vehicle programs, on component benches, mini benches, partial and full test benches, and production vehicles. I take requirements and architectural specifications and turn them into validation coverage, test strategies and test cases &mdash; about 3,100 of them on one program &mdash; and I keep traceability from the requirement through to the executed test, using IBM DOORS and JAMA. When something doesn't behave, I reproduce it, characterize it and work it down with PRA, RCA, Fault Tree, Fishbone and 5-Why alongside the people who own the design, then report validation status, defect trends and quality metrics to program leadership. I also led a distributed 14-person validation team on one program, which mostly taught me how to keep several integration problems moving at once and write a finding down clearly enough that the next engineer can act on it.",
            "Before Ford I spent three and a half years at Danlaw building HIL benches for GM's Global A and Global B platforms &mdash; subsystem simulation models in Danlaw Mx-Suite/MxVDev integrated with Vector VN-1630 interfaces so simulation and physical ECUs could exercise each other over CAN/CAN-FD. A good share of that work was chasing integration defects across company lines with OEM and supplier teams, and Magna was one of the supplier teams I worked with on those programs, so the supplier-facing side of this role is familiar ground.",
            "One honest gap: I have not owned a formal DVP&R or DFMEA document set, I have not run a program through launch end to end, and I have not worked with CAD, CAE simulation or FMVSS/ECE regulatory requirements. Those are real and I would be learning them with you. What I bring from day one is validation planning from requirements, vehicle-level integration and validation, requirements traceability, and cross-functional root-cause work. I'd welcome the chance to talk about whether that is the right starting point. Thank you for your time.",
        ],
    ),
    "gentex_pqe": dict(
        folder="Gentex_Production_Quality_Engineer_REQ026896_2026-10-16",
        summary=(
            "Automotive validation engineer with 9+ years in the industry &mdash; 5.5 years at Ford across five Ford and "
            "Lincoln vehicle programs and 3.5 years of HIL validation for General Motors, plus in-vehicle infotainment and "
            "ADAS feature validation before that. My work is problem-solving on real vehicles: I reproduce reported "
            "failures, characterize what the system actually did, and drive them to root cause with PRA, RCA, Fault Tree "
            "Analysis, Fishbone and 5-Why alongside the engineers who own the design &mdash; then verify that the corrective "
            "action actually held. I have owned requirements-based validation across bench and vehicle environments, "
            "authored roughly 3,100 test cases on one program, maintained requirements traceability end to end in IBM "
            "DOORS and JAMA, reported defect trends and quality metrics to program leadership, and led a distributed "
            "14-person validation team. I live in Farmington Hills and am looking for on-site quality engineering work in "
            "Michigan."
        ),
        skills=[
            ("Quality Engineering &amp; Root-Cause Problem Solving", "Formal Problem-Solving Tools (PRA, RCA, Fault Tree Analysis, Fishbone, 5-Why) &bull; Root-Cause Analysis &amp; Corrective-Action Verification &bull; Failure Containment, Reproduction &amp; Characterization &bull; Defect-Trend &amp; Quality-Metric Reporting &bull; Risk Assessment of Field and System Failures &bull; Continuous-Improvement Work (test repeatability, automation reuse)"),
            ("Validation &amp; Test Engineering", "Component-, Subsystem-, System- &amp; Vehicle-Level Validation &bull; Electrical &amp; Electronic System Behaviour Validation &bull; Requirements-Based Test Planning, Strategies &amp; Test Cases &bull; Regression &amp; Stability Validation &bull; Component Benches, Mini Benches, Partial/Full Test Benches &amp; Production Vehicles &bull; Production-Release Support &bull; Fix Verification"),
            ("Requirements, Documentation &amp; Traceability", "IBM DOORS &amp; JAMA Requirements Traceability (RTM) &bull; Approximately 3,100 Requirements-Based Test Cases Authored &bull; Test Procedures, Validation Reports &amp; Findings Documentation &bull; Change-Impact Analysis &bull; JIRA, Confluence, TestRail"),
            ("Automotive Programs &amp; Cross-Functional Work", "Five Ford &amp; Lincoln Vehicle Programs (FNV2/SYNC 4, FNV3, FNV3.X, FNV4) &bull; GM Global A &amp; Global B Platforms (HIL) &bull; Cross-Functional Problem Solving with Design, Software, Supplier &amp; Program Teams &bull; Supplier Issue Troubleshooting (including Magna, Valeo, LG Electronics) &bull; Distributed Team Leadership (14+) &bull; ISO 26262 Functional Safety (awareness-level training)"),
            ("Vehicle Networks &amp; Diagnostics", "CAN/CAN-FD Monitoring, Signal Analysis &amp; Fault Data &bull; DBC/ARXML Configuration &bull; ECU Diagnostics &amp; System-Response Analysis &bull; QNX and Android AOS Environments &bull; ValueCAN4, RadMoon, Vector VN-1630"),
            ("Tools", "Python Test Automation (OOP) &bull; MATLAB/Simulink, NI LabVIEW &bull; Microsoft Office Suite &bull; Git, JIRA, Confluence, TestRail &bull; AI-Assisted Tooling (GitHub Copilot, OpenCode)"),
        ],
        project_order=["fnv3", "fnv2", "gm_hil", "fnv4", "pisquare"],
        cover_company="Gentex Corporation",
        cover_addr="Zeeland, Michigan",
        cover_date="October 16, 2026",
        cover_paras=[
            "I'd like to apply for the Production Quality Engineer role in Zeeland. What caught my attention is that the core of the job &mdash; taking a reported failure, containing it, finding out what actually happened, and driving the fix through people who own the process &mdash; is what I have been doing for nine years. My version of it has been on the vehicle side rather than the plant floor, and I would like to move that skill set into manufacturing quality.",
            "At Ford I run component-, subsystem-, system- and vehicle-level validation on five Ford and Lincoln programs. When something shows up in the field or on a bench, I reproduce it, characterize it with CAN/CAN-FD data, and work it down with PRA, RCA, Fault Tree Analysis, Fishbone and 5-Why alongside the engineers who own the design &mdash; I don't hand off a symptom, I hand off the failure mechanism and the evidence. I then verify that the corrective action actually solves the problem, and I report defect trends and quality metrics to program leadership. Before Ford I spent three and a half years at Danlaw building HIL benches for GM's Global A and Global B platforms, which is where I did most of my cross-company defect troubleshooting with OEM and supplier teams, including Magna, Valeo and LG Electronics.",
            "Two things from that work transfer directly to a production quality role: prioritizing which problems actually matter, and communicating issues with data rather than opinion. I've led a distributed 14-person validation team, run defect triage across design, software and supplier groups, and driven continuous improvement into how testing is done &mdash; reusable automation templates, repeatable regression coverage, and documented frameworks other engineers could pick up and use.",
            "One honest gap: I have not worked on a plant floor. I have no PPAP, SPC, MSA or IATF 16949 experience, I have not owned warranty-return containment, and I have not used CT+ or BI. Those are real and I would be learning them with you, on site in Zeeland. What I bring on day one is disciplined problem solving on automotive hardware and software, corrective-action verification, defect-trend analysis, and requirements-to-evidence traceability. I'd welcome the chance to talk about whether that is a useful starting point. Thank you for your time.",
        ],
    ),
    "paccar_eve": dict(
        folder="PACCAR_Electrical_Validation_Engineer_1448211133_2026-10-16",
        summary=(
            "Automotive validation engineer with 9+ years in the industry, working on electrical, electronic and "
            "embedded control systems. I have run component-, subsystem-, system- and vehicle-level validation on "
            "five Ford and Lincoln vehicle programs and three and a half years of HIL validation for General Motors, "
            "and the shape of the work is the same every time: take the requirements and design inputs, turn them into "
            "validation plans and test cases, set up and instrument the bench or the vehicle, collect and analyze what "
            "the system actually did, then document it with conclusions and recommendations. I work hands-on with "
            "CAN/CAN-FD interfaces (ValueCAN4, RadMoon, Vector VN-1630), data acquisition boards and sensor and signal "
            "monitoring, and I use digital multimeters and oscilloscopes when something misbehaves. Roughly 3,100 of my "
            "test cases on one program were requirements-based, with traceability maintained end to end in IBM DOORS "
            "and JAMA, and I have led a distributed 14-person validation team."
        ),
        skills=[
            ("Electrical &amp; Embedded Control System Validation", "Vehicle Electrical Components &amp; Systems Validation &bull; Embedded Control System Behaviour Validation &bull; Component-, Subsystem-, System- &amp; Vehicle-Level Validation &bull; System-Response Analysis against Requirements &bull; Fault Reproduction, Root-Cause Analysis &amp; Fix Verification &bull; Production-Release Support"),
            ("Test Planning &amp; Validation Reporting", "Requirements-Based Test Plans, Strategies, Test Case Design &amp; Coverage &bull; Approximately 3,100 Requirements-Based Test Cases Authored &bull; Data Collection, Analysis &amp; Test Reports with Conclusions and Recommendations &bull; Test-Method Development and Improvement &bull; IBM DOORS &amp; JAMA Traceability (RTM) &bull; Change-Impact Analysis"),
            ("Instrumentation &amp; Data Acquisition", "CAN/CAN-FD Interfaces (ValueCAN4, RadMoon, Vector VN-1630) &bull; Data Acquisition Boards &amp; Sensor/Signal Monitoring &bull; Digital Multimeters &amp; Oscilloscopes &bull; Arduino Microcontrollers &bull; NI LabVIEW, MATLAB/Simulink &bull; Data Logging and Log Analysis"),
            ("Vehicle Networks &amp; Diagnostics", "CAN/CAN-FD Signal Monitoring and Analysis &bull; DBC/ARXML Configuration &bull; ECU Diagnostics &amp; System-Response Analysis (UDS, DoIP) &bull; Automotive Ethernet (100BASE-T1) &bull; LIN &bull; Fault Data Capture and Interpretation &bull; QNX and Android AOS Environments"),
            ("Test Environments &amp; Automation", "Component Benches, Mini Benches, Partial/Full Test Benches &amp; Production Vehicles &bull; Test Setup, Instrumentation Verification &amp; Preliminary Data Checks &bull; Repeatable Regression and Stability Testing &bull; Python (OOP) Test Automation, Reusable Frameworks &bull; Data-Driven and Slash-Based Test Methodology"),
            ("Programs, Root-Cause &amp; Cross-Functional Work", "Five Ford &amp; Lincoln Vehicle Programs (FNV2/SYNC 4, FNV3, FNV3.X, FNV4) &bull; GM Global A &amp; Global B HIL Platforms (Danlaw Mx-Suite/MxVDev) &bull; PRA, RCA, Fault Tree Analysis, Fishbone, 5-Why &bull; Cross-Functional Work with OEM Customer and Tier-1 Supplier Engineering Teams (Magna, Valeo, LG Electronics) &bull; Distributed Team Leadership (14+) &bull; ISO 26262 Functional Safety (awareness-level training) &bull; JIRA, Confluence, TestRail"),
        ],
        project_order=["fnv3", "gm_hil", "fnv2", "fnv4", "pisquare"],
        cover_company="PACCAR Inc.",
        cover_addr="PACCAR Technical Center &mdash; Mount Vernon, Washington",
        cover_date="October 16, 2026",
        cover_paras=[
            "I'd like to apply for the Electrical Validation Engineer role at the PACCAR Technical Center. The description reads like my normal working day: define the test requirements, build and instrument the lab setup, run the test, analyze what the hardware and embedded controls actually did, and write it down so the next person can use it. My experience is vehicle electrical and embedded control validation rather than a single lab bench, but the work itself is what I do.",
            "At Ford I run validation across five Ford and Lincoln vehicle programs at component, system and vehicle level. I configure and prepare the bench &mdash; hardware, software, communication interfaces, test configuration &mdash; execute CAN/CAN-FD signal monitoring and data acquisition, and analyze system response against the requirement. When a test fails I reproduce it, characterize it, and work it to root cause with the design and software owners. Before Ford I spent three and a half years at Danlaw building and running HIL benches for GM's Global A and Global B platforms in Danlaw Mx-Suite/MxVDev with Vector VN-1630 interfaces, which is where most of my bench setup, DBC/ARXML signal configuration and ECU response analysis came from.",
            "Two things in the posting that I do constantly: owning a validation project end to end &mdash; plan, setup, execution, data, and a report with conclusions and recommendations &mdash; and using bench equipment properly. Multimeters, oscilloscopes, DAQ boards and CAN interfaces are tools I use rather than tools I have read about. I have also maintained requirements traceability in IBM DOORS and JAMA, authored about 3,100 requirements-based test cases on one program, and produced validation reports and defect-trend summaries that program leadership acted on.",
            "One honest gap: my degrees are a B.Tech in Aeronautical Engineering and an M.S. in Mechanical Engineering, not Electrical Engineering, and I have not worked with J1939 in particular. My CAN/CAN-FD work has been on automotive vehicle networks rather than heavy-truck J1939 specifically, so the protocol details would be new to me. The bench discipline, the instrumentation and the validation method are not. I'd welcome the chance to talk about the role. Thank you for your time.",
        ],
    ),
    "zf_adas": dict(
        folder="ZF_Senior_ADAS_Application_Engineer_91317_2026-10-16",
        summary=(
            "Automotive validation engineer with 9+ years in the industry, validating electrical and electronic vehicle "
            "systems &mdash; 5.5 years at Ford across five Ford and "
            "Lincoln vehicle programs and 3.5 years of HIL validation for General Motors, plus in-vehicle infotainment "
            "and driver-assist feature validation before that. I read technical requirements and specifications and turn "
            "them into validation coverage, and when a requirement and an implementation disagree I document the "
            "deviation, work out what it actually affects, and drive it to resolution with the engineers who own the "
            "design. I maintain traceability end to end in IBM DOORS and JAMA, have authored roughly 3,100 "
            "requirements-based test cases on one program, and use CAN/CAN-FD signal analysis, diagnostics and data "
            "acquisition daily to prove what a system actually did. I have led a distributed 14-person validation team "
            "and drive failures to root cause with PRA, RCA, Fault Tree Analysis, Fishbone and 5-Why."
        ),
        skills=[
            ("Requirements, Specifications &amp; Deviation Handling", "Technical Requirement and Specification Intake &bull; Customer-vs-Internal Specification Comparison, Mapping &amp; Deviation Identification &bull; Change-Request Preparation and Impact Breakdown &bull; Requirements Traceability (IBM DOORS, JAMA, RTM) &bull; Testability and Acceptance-Criteria Review &bull; Change-Impact Analysis"),
            ("Validation &amp; Verification Engineering", "Component-, Subsystem-, System- &amp; Vehicle-Level Validation &bull; Requirements-Based Test Planning, Test Case Design and Coverage &bull; Regression and Stability Validation &bull; Fix Verification &amp; Production-Release Support &bull; Approximately 3,100 Requirements-Based Test Cases Authored"),
            ("ADAS, Infotainment &amp; Vehicle Feature Validation", "In-Vehicle Validation of HUD, Bluetooth and Cluster Connectivity Features and ADAS-Related Features &bull; Feature Behaviour vs Requirement on Bench and Vehicle &bull; Integration Troubleshooting with Design, Software and Supplier Teams &bull; Vehicle Spy, CANoe, CANalyzer"),
            ("Vehicle Networks, Diagnostics &amp; Data", "CAN/CAN-FD Signal Monitoring and Analysis (ValueCAN4, RadMoon, Vector VN-1630) &bull; Automotive Ethernet &bull; LIN &bull; DBC/ARXML Configuration &bull; ECU Diagnostics and System-Response Analysis &bull; Sensor/Signal Monitoring, Data Acquisition, Log Analysis and Defect Evidence &bull; QNX and Android AOS Environments"),
            ("Root-Cause &amp; Cross-Functional Resolution", "PRA, RCA, Fault Tree Analysis, Fishbone, 5-Why &bull; Failure Reproduction and Characterization &bull; Cross-Functional Resolution with OEM, Tier-1 and Supplier Teams (Magna, Valeo, LG Electronics) &bull; Deviation and Issue Escalation with Evidence &bull; Distributed Team Leadership (14+) &bull; ISO 26262 Functional Safety (awareness-level training)"),
            ("Tools &amp; Documentation", "Python (OOP) Test Automation &bull; MATLAB/Simulink, NI LabVIEW, Danlaw Mx-Suite/MxVDev &bull; Technical Documentation and Validation Reporting &bull; JIRA, Confluence, TestRail &bull; Git &bull; Microsoft Office Suite"),
        ],
        project_order=["fnv3", "pisquare", "gm_hil", "fnv2", "fnv4"],
        cover_company="ZF Group &mdash; Commercial Vehicle Solutions",
        cover_addr="Auburn Hills, Michigan",
        cover_date="October 16, 2026",
        cover_paras=[
            "I'd like to apply for the Senior ADAS Application Engineer role in Auburn Hills. I want to be straight about one thing up front: my career has been on the validation side of the fence rather than application engineering, so this is a deliberate move toward customer-requirement and product-matching work rather than a continuation of the same job.",
            "What I do today that maps onto it: I read technical specifications, both customer requirements and internal system and architectural documents, and turn them into validation coverage. When a requirement and an implementation disagree, I document the deviation, work out what it actually affects, and drive it to resolution with the product, software and supplier engineers. At Ford that has been across five Ford and Lincoln vehicle programs, and before that three and a half years building HIL benches for GM's Global A and Global B platforms, which is where most of my cross-company troubleshooting with Magna, Valeo and LG Electronics happened. Earlier, at Pi-Square, I validated driver-assist, HUD and cluster features in vehicle with CAN bus analysis.",
            "The parts of the posting I have not done: I have never owned the mapping of customer specifications to ZF specifications, never produced drawings, schematics or bills of material for a customer application, never owned product parameter configuration, and I have no commercial-vehicle experience with Class 6-8 trucks and buses. I also have not done camera or radar sensor calibration. Those are real gaps and I would be learning them from the product group.",
            "What I would bring is the systems-level view of how these features behave across bench and vehicle, the habit of resolving technical disagreements with evidence rather than opinion, and nine years in automotive validation with the traceability and documentation discipline that goes with it. I'd welcome the chance to talk about whether that is a useful starting point. Thank you for your time.",
        ],
    ),
    "dana_qe": dict(
        folder="Dana_Quality_Engineer_66322_2026-10-16",
        summary=(
            "Automotive validation engineer with 9+ years in the industry &mdash; 5.5 years at Ford across five Ford and "
            "Lincoln vehicle programs and 3.5 years of HIL validation for General Motors, plus in-vehicle infotainment "
            "and ADAS feature validation before that. My work is problem-solving on real vehicles: I reproduce reported "
            "failures, characterize what the system actually did, and drive them to root cause with PRA, RCA, Fault Tree "
            "Analysis, Fishbone and 5-Why alongside the engineers who own the design &mdash; then verify that the "
            "corrective action actually held. I have owned requirements-based validation across bench and vehicle "
            "environments, authored roughly 3,100 test cases on one program, maintained requirements traceability end to "
            "end in IBM DOORS and JAMA, reported defect trends and quality metrics to program leadership, and led a "
            "distributed 14-person validation team. I live in Farmington Hills, Michigan and want to move my validation "
            "and root-cause background into manufacturing quality."
        ),
        skills=[
            ("Quality &amp; Root-Cause Problem Solving", "Formal Problem-Solving Tools (PRA, RCA, Fault Tree Analysis, Fishbone, 5-Why) &bull; Root-Cause Analysis &amp; Corrective-Action Verification &bull; Failure Containment, Reproduction &amp; Characterization &bull; Defect-Trend &amp; Quality-Metric Reporting &bull; Risk Assessment of Field and System Failures &bull; Continuous-Improvement Work (test repeatability, automation reuse)"),
            ("Validation &amp; Test Engineering", "Component-, Subsystem-, System- &amp; Vehicle-Level Validation &bull; Electrical &amp; Electronic System Behaviour Validation &bull; Requirements-Based Test Planning, Strategies &amp; Test Cases &bull; Regression &amp; Stability Validation &bull; Component Benches, Mini Benches, Partial/Full Test Benches &amp; Production Vehicles &bull; Production-Release Support &bull; Fix Verification"),
            ("Requirements, Documentation &amp; Traceability", "IBM DOORS &amp; JAMA Requirements Traceability (RTM) &bull; Design, Specification and Requirement Review Participation &bull; Approximately 3,100 Requirements-Based Test Cases Authored &bull; Test Procedures, Validation Reports &amp; Findings Documentation &bull; Change-Impact Analysis &bull; JIRA, Confluence, TestRail"),
            ("Automotive Programs &amp; Cross-Functional Work", "Five Ford &amp; Lincoln Vehicle Programs (FNV2/SYNC 4, FNV3, FNV3.X, FNV4) &bull; GM Global A &amp; Global B Platforms (HIL) &bull; Cross-Functional Problem Solving with Design, Software, OEM Customer, Supplier &amp; Program Teams &bull; Supplier and Customer Issue Troubleshooting (including Magna, Valeo, LG Electronics) &bull; Distributed Team Leadership (14+) &bull; ISO 26262 Functional Safety (awareness-level training)"),
            ("Vehicle Networks &amp; Diagnostics", "CAN/CAN-FD Monitoring, Signal Analysis &amp; Fault Data &bull; DBC/ARXML Configuration &bull; ECU Diagnostics &amp; System-Response Analysis &bull; QNX and Android AOS Environments &bull; ValueCAN4, RadMoon, Vector VN-1630"),
            ("Tools", "Python Test Automation (OOP) &bull; MATLAB/Simulink, NI LabVIEW &bull; Microsoft Office Suite &bull; Git, JIRA, Confluence, TestRail &bull; AI-Assisted Tooling (GitHub Copilot, OpenCode)"),
        ],
        project_order=["fnv3", "fnv2", "gm_hil", "fnv4", "pisquare"],
        cover_company="Dana Incorporated",
        cover_addr="Henderson, Kentucky",
        cover_date="October 16, 2026",
        cover_paras=[
            "I'd like to apply for the Quality Engineer role in Henderson. What caught my attention is that the core of the job &mdash; taking a reported failure, containing it, finding out what actually happened, and driving the fix through the people who own the process &mdash; is what I have been doing for nine years. My version of it has been on the vehicle side rather than the plant floor, and I want to move that skill set into production quality.",
            "At Ford I run component-, subsystem-, system- and vehicle-level validation on five Ford and Lincoln programs. When something shows up in the field or on a bench, I reproduce it, characterize it with CAN/CAN-FD data, and work it down with PRA, RCA, Fault Tree Analysis, Fishbone and 5-Why alongside the engineers who own the design &mdash; I don't hand off a symptom, I hand off the failure mechanism and the evidence. I then verify that the corrective action actually solves the problem, and I report defect trends and quality metrics to program leadership. Before Ford I spent three and a half years at Danlaw building HIL benches for GM's Global A and Global B platforms, where most of my cross-company defect troubleshooting was with OEM and supplier teams, including Magna, Valeo and LG Electronics.",
            "Two things from that work transfer directly to a quality role: prioritizing which problems actually matter, and communicating issues with data rather than opinion. I have led a distributed 14-person validation team, run defect triage across design, software and supplier groups, and driven continuous improvement into how testing is done &mdash; reusable automation templates, repeatable regression coverage, and documented frameworks other engineers could pick up and use.",
            "One honest gap: I have not worked on a plant floor. I have no APQP, PPAP, PFMEA, SPC, MSA or IATF 16949 experience, no GD&amp;T or gage R&amp;R work, and I have not owned production-part qualification or warranty-return containment. Those are real, and I would be learning them from the quality team in Henderson. What I would bring on day one is disciplined problem solving on automotive hardware and software, corrective-action verification, defect-trend reporting, and requirements-to-evidence traceability. I'd welcome the chance to talk about whether that is a useful starting point. Thank you for your time.",
        ],
    ),
    "aurora_rel": dict(
        folder="Aurora_Staff_HW_Reliability_Engineer_ce29977c_2026-10-17",
        summary=(
            "Automotive validation and reliability engineer with 9+ years in hardware validation and "
            "reliability testing of vehicle electronics &mdash; on component benches, hardware-in-the-loop "
            "rigs and production vehicles. 5.5 years at Ford across five Ford and Lincoln vehicle programs "
            "and 3.5 years of HIL validation for General Motors. My work is failure-driven: I reproduce "
            "field-reported failures under known conditions, characterize them with CAN/CAN-FD data and "
            "measurement equipment, work them to root cause with PRA, RCA, Fault Tree, Fishbone and 5-Why "
            "analysis, and drive corrective actions to closure with the design, firmware and software "
            "engineers and suppliers who own the fix &mdash; including LG Electronics, Magna and Valeo. "
            "I plan and execute test campaigns across bench and vehicle environments, set pass/fail limits "
            "with test and design teams, analyze failure-pattern and quality-metric data for trends, and "
            "document procedures and results so the next engineer can repeat them. I'd like to bring that "
            "failure-analysis discipline to autonomous-vehicle hardware."
        ),
        skills=[
            ("Failure Analysis &amp; Reliability", "Failure Reproduction &amp; Characterization (bench, vehicle &amp; field-reported) &bull; Root-Cause Analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) &bull; Fault-Tree-Based Risk Analysis Sessions &bull; Corrective-Action Verification &amp; Closure &bull; Defect-Trend &amp; Failure-Pattern Analysis"),
            ("Hardware &amp; System Validation", "Component-, System- &amp; Vehicle-Level Hardware Validation &bull; Electrical &amp; Electronic System-Behaviour Validation &bull; Functional, Regression, Stability &amp; Durability Testing &bull; Pass/Fail Limit &amp; Test-Parameter Definition &bull; Requirements-Based Test Cases (~3,100 in one program) &bull; Production-Release Support"),
            ("Measurement &amp; Data Analysis", "Data Acquisition &amp; Signal Monitoring &bull; Oscilloscopes, Digital Multimeters, DAQ Boards &bull; CAN/CAN-FD Signal &amp; System-Response Analysis (ValueCAN4, RadMoon) &bull; Quality-Metric &amp; Failure-Trend Reporting"),
            ("Test Environments", "Component, Mini &amp; Full Test Benches &bull; Hardware-in-the-Loop Rigs (Danlaw Mx-Suite/MxVDev, Vector VN-1630) &bull; Production Vehicles &bull; Bench &amp; Vehicle Bring-Up &bull; QNX &amp; Android AOS Multi-OS Platforms"),
            ("Vehicle Networks &amp; Diagnostics", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; UDS &amp; DoIP &bull; DBC / ARXML Signal Configuration &bull; CANoe / CANalyzer, Vehicle Spy &bull; ADAS Perception Sensor Overview (camera, radar, LiDAR)"),
            ("Cross-Functional &amp; Tools", "OEM&ndash;Supplier Troubleshooting (LG Electronics, Magna, Valeo) &bull; Cross-Disciplinary Work with Hardware, Firmware, Thermal &amp; Software Teams &bull; Distributed Team Leadership (14+) &bull; Python Automation (OOP) &bull; MATLAB/Simulink, NI LabVIEW &bull; JIRA, JAMA, IBM DOORS, Confluence, TestRail &bull; ISO 26262 Functional-Safety Awareness"),
        ],
        project_order=["fnv3", "gm_hil", "fnv4", "fnv2", "pisquare"],
        cover_company="Aurora Innovation",
        cover_addr="Mountain View, California",
        cover_date="October 17, 2026",
        cover_paras=[
            "I'm applying for the Staff Hardware Reliability Engineer role on the Hardware Reliability team. The part of the job that fits me best &mdash; proving why hardware fails, driving it to a documented root cause, and making sure the corrective action actually holds &mdash; is what I have been paid to do for nine years, and I'd like to do it on the hardware behind the Aurora Driver.",
            "At Ford I run component-, system- and vehicle-level validation across five Ford and Lincoln programs, on benches and on production vehicles. When something misbehaves I reproduce it under known conditions, characterize it with CAN/CAN-FD data and an oscilloscope or multimeter, and work it down with PRA, RCA, Fault Tree, Fishbone and 5-Why analysis until the failure mechanism is understood &mdash; then verify the fix and track the trend. Setting pass/fail limits with the test and design teams, and documenting the setup and procedure so someone else can repeat the campaign, is part of how I work.",
            "Before Ford I spent three and a half years at Danlaw building and running HIL benches for GM's Global A and Global B platforms &mdash; Mx-Suite/MxVDev simulation integrated with Vector VN-1630 so it could talk to physical ECUs over CAN/CAN-FD. Those benches had to be electrically sound and repeatable before any test ran on them, and most of my cross-company failure work ran through OEM and supplier teams like LG Electronics, Magna and Valeo. Debugging across the electrical, mechanical and software layers at once became second nature there.",
            "I'll be honest about the edges: I have not built predictive failure-rate models, I have not run environmental stress campaigns &mdash; thermal chambers, shock and vibration &mdash; and I have not worked in a mass-production manufacturing environment or facilitated DFMEA sessions. What I bring on day one is nine years of failure analysis on automotive electronics and software, disciplined test-campaign execution, and the habit of writing down what was tested, how and what it showed. I'd welcome the chance to talk about whether that is a useful starting point for the team. Thank you for your time.",
        ],
    ),
    "rivian_qa": dict(
        folder="Rivian_Sr_Audio_SW_QA_Engineer_34172_2026-10-17",
        summary=(
            "Software validation engineer with 9+ years testing embedded and in-vehicle software, including "
            "5.5 years at Ford on the SYNC 4 infotainment platform and the FNV vehicle programs and 3.5 "
            "years of HIL validation for General Motors. I build and maintain the automated tests that gate "
            "software releases: Python-based functional, regression and stability frameworks, run "
            "repeatably across bench and vehicle environments, with results analyzed for failure patterns "
            "and reported as defect trends. I have validated infotainment and system software across QNX "
            "and Linux-based Android AOSP environments &mdash; HMI features, power management, host/guest OS "
            "interactions &mdash; debugged software and communication defects with CAN tools on "
            "hardware-in-the-loop rigs and production vehicles, and authored roughly 3,100 requirements-based "
            "test cases in one program. TestRail, JIRA, DOORS and JAMA for case management and traceability."
        ),
        skills=[
            ("Test Automation", "Python Test Automation (OOP) &bull; Automated Regression, Functional &amp; Stability Testing &bull; Reusable, Data-Driven &amp; Slash-Based Test Frameworks &bull; Automated Build-Verification &amp; Repeatable Regression Runs &bull; Test-Result &amp; Failure-Pattern Analysis"),
            ("Infotainment &amp; System Software Validation", "SYNC 4 Infotainment Validation (F-150, Mustang Mach-E, F-150 Lightning) &bull; HMI &amp; System-Layer Feature Validation &bull; QNX &amp; Linux-Based Android AOSP Multi-OS Environments &bull; Host/Guest OS Interaction &bull; Power-Management Stability &amp; Regression Testing"),
            ("Test Design &amp; Management", "Requirements-Based Test Cases (~3,100 in one program) &bull; Functional, Regression, Integration &amp; Smoke Testing &bull; TestRail &bull; Requirements Traceability (IBM DOORS, JAMA) &bull; Defect Triage, Root Cause &amp; Fix Verification"),
            ("HIL &amp; Bench Environments", "Hardware-in-the-Loop Rigs (Danlaw Mx-Suite/MxVDev, Vector VN-1630) &bull; Component, Mini &amp; Full Test Benches &bull; Production-Vehicle Testing &bull; Bench-to-Vehicle Release Validation &bull; ECU &amp; System-Response Analysis"),
            ("Networks &amp; Debug", "CAN / CAN-FD Signal Validation &bull; Vehicle Network Debugging (Vehicle Spy, CANoe/CANalyzer, ValueCAN4, RadMoon) &bull; Root-Cause Analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) &bull; ISO 26262 Awareness"),
            ("Tools", "MATLAB/Simulink, NI LabVIEW &bull; Git, JIRA, Confluence &bull; Agile / Scrum &bull; Distributed Team Leadership (14+) &bull; AI-Assisted Tooling (GitHub Copilot, OpenCode)"),
        ],
        project_order=["fnv2", "fnv3", "fnv4", "gm_hil", "pisquare"],
        cover_company="Rivian",
        cover_addr="Palo Alto, California",
        cover_date="October 17, 2026",
        cover_paras=[
            "I'm applying for the Sr. Audio Software Quality Assurance Engineer role with Rivian's Audio Group. I have spent nine years on the software-validation side of in-vehicle systems &mdash; infotainment included &mdash; and the core of this job, owning the automated regression suite that decides whether a software release ships, is work I already do and want to go deeper on.",
            "At Ford I validate software across bench and production-vehicle environments on five Ford and Lincoln programs, including two years owning SYNC 4 validation on the F-150, Mustang Mach-E and F-150 Lightning. I write and maintain Python-based functional, regression and stability automation &mdash; reusable, data-driven frameworks other component teams pick up and use &mdash; and I run them as repeatable build-verification and regression passes, then analyze the results for failure patterns and report defect trends to feature owners and program leadership. I have worked AOSP and QNX environments side by side, including host/guest OS interactions and power-management stability, and I am comfortable living in the gap between the software, DSP-adjacent and vehicle teams when something behaves differently than the requirement says it should.",
            "Before Ford I spent three and a half years at Danlaw on HIL rigs for GM's Global A and Global B platforms &mdash; Mx-Suite/MxVDev with Vector VN-1630 talking to physical ECUs over CAN/CAN-FD &mdash; where I ran regression validation, analyzed ECU responses and chased integration defects to root cause. I author test cases from requirements and keep traceability in TestRail, DOORS and JAMA; roughly 3,100 in one program is the largest set I have owned.",
            "The honest gaps: I have never tested audio DSP signal chains, I have not used Audio Precision or SoundCheck hardware, and I have not owned a CI/CD pipeline in Jenkins or GitLab &mdash; my automation has run as scheduled and on-demand suites rather than inside a build pipeline. What transfers on day one is the test-framework ownership, the regression discipline across bench and vehicle, the multi-OS debugging, and the triage habits. I'd welcome the chance to talk about that. Thank you for your time.",
        ],
    ),
    "applied_integ": dict(
        folder="AppliedIntuition_SW_Integration_Customer_Onsite_d6560e7d_2026-10-17",
        summary=(
            "Systems integration and validation engineer with 9+ years in automotive, most of it spent "
            "standing up the thing that has to work before anyone else can test &mdash; benches, vehicle "
            "setups and the communication layers they run on. 5.5 years at Ford across five vehicle programs "
            "and 3.5 years of HIL validation for General Motors. I prepare and bring up component and system "
            "test benches &mdash; hardware, software, communication interfaces and test configuration "
            "&mdash; then validate that the integrated system behaves as required: monitoring CAN/CAN-FD "
            "traffic, capturing data with DAQ equipment, and diagnosing integration faults hands-on with "
            "oscilloscopes and multimeters. I debug across the electrical, mechanical and software layers at "
            "once, work integration issues to root cause with OEM and supplier engineering teams, and write "
            "the setup and test procedures other engineers use."
        ),
        skills=[
            ("Bench &amp; Vehicle Bring-Up", "Component, Mini &amp; Full Test Bench Preparation &amp; Bring-Up &bull; Hardware, Communication-Interface &amp; Test-Configuration Setup &bull; Build Retrieval, Flashing &amp; Sanity Testing &bull; Production-Vehicle Test Setup &bull; Power-Management &amp; State-Transition Validation (QNX, Android AOSP)"),
            ("Vehicle Networks", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; UDS &amp; DoIP &bull; DBC / ARXML Signal Configuration &bull; CANoe / CANalyzer, Vehicle Spy &bull; ValueCAN3/4, RadMoon, Rad-Galaxy"),
            ("Integration Debug &amp; Root Cause", "Electrical, Mechanical &amp; Software Integration Debugging &bull; Failure Reproduction &amp; Characterization &bull; Root-Cause Analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) &bull; ECU &amp; System-Response Analysis &bull; Corrective-Action Validation"),
            ("Validation &amp; Test", "Component-, System- &amp; Vehicle-Level Validation &bull; HIL Rigs (Danlaw Mx-Suite/MxVDev, Vector VN-1630) &bull; Functional, Regression &amp; Stability Testing &bull; Requirements-Based Test Cases (~3,100) &bull; Pass/Fail Limit Definition"),
            ("Customer &amp; Cross-Functional", "OEM&ndash;Supplier Onsite Collaboration (LG Electronics, Magna, Valeo) &bull; Distributed Team Leadership (14+) &bull; Installation, Setup &amp; Test Procedures for Knowledge Transfer &bull; Agile / Scrum"),
            ("Tools", "Python Automation (OOP) &bull; MATLAB/Simulink, NI LabVIEW &bull; JIRA, JAMA, IBM DOORS, Confluence, TestRail &bull; Git &bull; AI-Assisted Tooling (GitHub Copilot, OpenCode)"),
        ],
        project_order=["fnv3", "gm_hil", "fnv2", "fnv4", "pisquare"],
        cover_company="Applied Intuition",
        cover_addr="Ann Arbor, Michigan",
        cover_date="October 17, 2026",
        cover_paras=[
            "I'm applying for the Software Integration Engineer, Customer Onsite role in Ann Arbor. Working out of a customer's development site, integrating your E/E platform on their benches and vehicles until it passes their acceptance &mdash; that is close to a literal description of the last nine years of my career, and being the technical person on site who owns the answer is the part of the job I do best.",
            "At Ford I prepare and bring up component- and system-level test benches &mdash; the required hardware, the communication interfaces, the test configuration &mdash; and then validate the integrated system on benches and across five production-vehicle programs. Day to day that means monitoring CAN/CAN-FD traffic with ValueCAN4 and RadMoon, flashing and sanity-checking builds, checking power modes and state transitions across QNX and Android AOS, and diagnosing why something does not come up the way the requirement says it should with a scope or a multimeter. When an integration issue crosses the electrical, mechanical and software boundaries &mdash; and it usually does &mdash; I reproduce it, characterize it and drive it to root cause with PRA, RCA, Fault Tree, Fishbone and 5-Why alongside the engineers who own that layer. I write down the setup and the procedure every time, because on a customer site the answer has to outlive the person who found it.",
            "Before Ford I spent three and a half years at Danlaw building HIL benches for GM's Global A and Global B platforms &mdash; Mx-Suite/MxVDev simulation integrated with Vector VN-1630 so simulated and physical ECUs could talk over CAN/CAN-FD &mdash; and most of my cross-company troubleshooting ran with OEM and supplier teams, including LG Electronics, Magna and Valeo. I have also led a distributed 14-person validation team, which is where I learned to be the single point of technical contact and keep a customer informed without overstating what the data shows.",
            "What I would bring on day one is nine years of bench and vehicle bring-up, integration debugging and customer-facing technical discipline in Michigan — including SOME/IP experience from the FNV4 program's adaptive AUTOSAR zonal architecture implementation. My network depth spans CAN, CAN-FD, LIN, UDS/DoIP, automotive Ethernet, and SOME/IP service-oriented communication. I'm eager to apply that to your platform. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),
    "rivian_hwtest": dict(
        folder="Rivian_Sr_HW_Test_Cleaning_Systems_34594_2026-10-17",
        summary=(
            "Hardware and software validation engineer with 9+ years designing, building and running the "
            "tests that prove automotive systems work &mdash; from component benches through production "
            "vehicles. 5.5 years at Ford across five Ford and Lincoln vehicle programs and 3.5 years "
            "building hardware-in-the-loop benches for General Motors. I own test execution end to end: "
            "characterizing hardware on the bench, instrumenting data-acquisition and CAN/CAN-FD logging "
            "setups (DAQ boards, oscilloscopes, digital multimeters, ValueCAN4, RadMoon), writing Python "
            "automation so campaigns run repeatably, analyzing results, and driving failed tests to "
            "documented root cause &mdash; PRA, RCA, Fault Tree, Fishbone, 5-Why &mdash; with the design, "
            "electrical and supplier teams who own the fix. I plan campaigns from requirements, set "
            "pass/fail limits with test and design teams, and keep cross-functional follow-through moving "
            "from test finding to agreed closure date. My validation has covered ADAS-related and "
            "connected features on production vehicles, and I'm building toward autonomy &mdash; "
            "ADAS/AD concepts, perception sensors, and ROS/ROS 2 and sensor-fusion fundamentals "
            "&mdash; because I'd like to bring this test discipline to an autonomous-vehicle program."
        ),
        skills=[
            ("Test Benches &amp; Environments", "Component, Mini &amp; Full Test Bench Design, Build &amp; Instrumentation &bull; Hardware-in-the-Loop Rigs (Danlaw Mx-Suite/MxVDev, Vector VN-1630) &bull; Bench Characterization &amp; Bring-Up &bull; Production-Vehicle Test Setup &bull; Component, System- &amp; Vehicle-Level Validation"),
            ("Data Acquisition &amp; Logging", "Data Acquisition (DAQ Boards, Oscilloscopes, Digital Multimeters) &bull; Instrumentation &amp; Signal Monitoring &bull; CAN / CAN-FD Logging (ValueCAN4, RadMoon) &bull; Signal &amp; System-Response Analysis &bull; Test-Result &amp; Failure-Pattern Analysis"),
            ("Test Automation &amp; Design", "Python Test Automation (OOP) &bull; Requirements-Based Test Cases (~3,100, authored from Requirements &amp; Architectural Specifications) &bull; Automated Regression, Functional &amp; Stability Testing &bull; Pass/Fail Limit &amp; Acceptance-Criteria Definition &bull; Design, Specification &amp; Requirement Review (Requirements vs. Implementation) &bull; TestRail, IBM DOORS, JAMA"),
            ("Root Cause &amp; Failure Analysis", "Root-Cause Analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) &bull; Failure Reproduction &amp; Characterization &bull; Corrective-Action Verification &amp; Closure &bull; Defect-Trend &amp; Failure-Pattern Reporting"),
            ("Vehicle Networks &amp; Diagnostics", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; CANoe / CANalyzer, Vehicle Spy &bull; DBC / ARXML Signal Configuration &bull; UDS &amp; DoIP &bull; ADAS Perception Sensor Overview (camera, radar, LiDAR) &bull; In-Vehicle Validation of ADAS-Related Features (HUD, Cluster, Driver-Assist)"),
            ("Cross-Functional &amp; Tools", "OEM&ndash;Supplier Troubleshooting (LG Electronics, Magna, Valeo) &bull; Cross-Disciplinary Work with Design, ADAS, EE &amp; Software Teams &bull; Distributed Team Leadership (14+) &bull; MATLAB/Simulink, NI LabVIEW &bull; JIRA, Confluence &bull; ISO 26262 Awareness"),
        ],
        project_order=["gm_hil", "fnv3", "fnv4", "fnv2", "pisquare"],
        cover_company="Rivian",
        cover_addr="Palo Alto, California",
        cover_date="October 17, 2026",
        cover_paras=[
            "I'm applying for the Sr. Hardware Test Engineer, Cleaning Systems role on the Electrical Hardware team. The shape of the job &mdash; owning test from bench characterization through vehicle-level validation, building and instrumenting the benches yourself, and turning failed tests into root cause and design changes on an L4 program &mdash; is a close description of what I have been paid to do for nine years on vehicle hardware and software.",
            "At Ford I run component-, system- and vehicle-level validation across five Ford and Lincoln programs, on benches and on production vehicles. That includes building and instrumenting the test setup, capturing data with DAQ boards, oscilloscopes and multimeters, and logging CAN/CAN-FD with ValueCAN4 and RadMoon while the test runs. I write Python automation so a campaign repeats the same way every time, plan test cases from requirements &mdash; roughly 3,100 in one program &mdash; set pass/fail limits with the test and design teams, and when something fails I reproduce it, characterize it and work it to root cause with PRA, RCA, Fault Tree, Fishbone and 5-Why alongside the design, electrical and supplier engineers who own the fix. Keeping the schedule side honest &mdash; test finding to agreed action to closure date &mdash; is part of that job, not a separate function.",
            "Before Ford I spent three and a half years at Danlaw building hardware-in-the-loop benches for GM's Global A and Global B platforms &mdash; Mx-Suite/MxVDev simulation integrated with Vector VN-1630 so simulated and physical ECUs could talk over CAN/CAN-FD. Those benches had to be specified, wired and proven before a single test ran on them, and I have also led a distributed 14-person validation team, which is where I learned to own a lab-like workflow: equipment, scheduling, data and follow-through.",
            "The honest gaps: I have never worked on sensor cleaning systems &mdash; no fluid or aerodynamic characterization, no nozzle, pump or airflow testing &mdash; I have not designed fixtures in CAD or done 3D printing and machining, and I have not owned a DVP&amp;R or facilitated a DFMEA. DOE-style statistical test planning and high-speed video capture are also not on my record. What I would bring on day one is nine years of bench and vehicle test execution, instrumentation and DAQ, Python test automation, and root-cause discipline on automotive hardware. I'd welcome the chance to talk about whether that is a useful starting point. Thank you for your time.",
        ],
    ),
    "gm_ivi_verif": dict(
        folder="GM_Infotainment_SW_Verification_JR-202622242_2026-10-17",
        summary=(
            "Software test and verification engineer with 9+ years executing and writing manual and "
            "automated test scripts for in-vehicle software &mdash; five and a half years at Ford across "
            "five Ford and Lincoln vehicle programs and three and a half years validating infotainment, "
            "HUD, cluster and ADAS-related features at Pi-Square Technologies. My day job is what this "
            "posting describes: verify infotainment component function and performance on benches and in "
            "production vehicles over CAN, CAN-FD, LIN and automotive Ethernet; configure benches for "
            "specific test scenarios; document defects with steps to reproduce, collected test logs and "
            "failures linked to requirements in IBM DOORS; develop and update requirements-based test "
            "cases (~3,100 in one program); run and plan verification cycles including regression, "
            "functional and stability suites; and drive defects to closure with systems, software, "
            "validation and supplier teams. Python is my automation language, I work daily in QNX, Android "
            "and Linux environments, and I diagnose over UDS/DoIP with CANoe, CANalyzer and Vehicle Spy."
        ),
        skills=[
            ("Infotainment &amp; IVI Verification", "In-Vehicle Infotainment Feature Verification (HUD, Bluetooth, Cluster, Connectivity) &bull; Bench &amp; In-Vehicle Validation of IVI and ADAS-Related Features &bull; Infotainment ECU Function &amp; Performance Testing &bull; Ford Connected &amp; Infotainment Features (5 Programs) &bull; Pi-Square IVI Validation (IBM DOORS Traceability)"),
            ("Test Automation &amp; Cases", "Manual &amp; Automated Test Script Execution &bull; Python Test Automation (OOP) &bull; Requirements-Based Test Cases (~3,100) &bull; Regression, Functional &amp; Stability Testing &bull; Defect Documentation: Repro Steps, Test Logs, Requirement Linking &bull; TestRail, JIRA"),
            ("Vehicle Electrical (E/E) Networks &amp; Diagnostics", "Vehicle Electrical Architecture &amp; E/E Network Validation (CAN / CAN-FD / LIN / Automotive Ethernet) &bull; CANoe / CANalyzer, Vehicle Spy, ValueCAN4 &bull; DBC / ARXML Signal Configuration &bull; UDS &amp; DoIP Diagnostics &bull; Diagnostic &amp; Network Testing"),
            ("OS, Platforms &amp; Benches", "QNX, Android (AOSP), Linux Environments &bull; HIL Rigs (Danlaw Mx-Suite/MxVDev, Vector VN-1630) &bull; Bench Configuration for Test Scenarios &bull; MATLAB/Simulink, NI LabVIEW &bull; Production-Vehicle Test Setup"),
            ("Verification Planning &amp; Triage", "Verification-Cycle Planning &amp; Scheduling &bull; Sanity &amp; Regression Suite Selection per Build &bull; Cross-Functional Defect Triage (Systems, Software, Validation, Suppliers) &bull; Status Reporting to Program Leadership &bull; Test Assignments Coordination (14+ Engineers)"),
            ("Requirements &amp; Root Cause", "Requirements Analysis &amp; Traceability (IBM DOORS, JAMA) &bull; Root-Cause Analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) &bull; Failure Reproduction &amp; Characterization &bull; Corrective-Action Verification &amp; Closure &bull; ISO 26262 Awareness"),
        ],
        project_order=["pisquare", "gm_hil", "fnv3", "fnv4", "fnv2"],
        cover_company="General Motors",
        cover_addr="Warren, Michigan",
        cover_date="October 17, 2026",
        cover_paras=[
            "I'm applying for the Infotainment Software Verification Engineer role in Warren. The duties section reads like the last nine years of my work life: executing manual and automated test scripts against infotainment function and performance requirements, configuring benches for specific scenarios, documenting defects with steps to reproduce, collected logs and failures linked to requirements, and planning the weekly verification cycle that keeps a program honest.",
            "At Pi-Square Technologies I validated in-vehicle infotainment and ADAS-related features &mdash; HUD, Bluetooth and cluster connectivity &mdash; on benches and in production vehicles, over CAN, CAN-FD, LIN and automotive Ethernet, using CANoe, CANalyzer and Vehicle Spy for monitoring and debugging, with requirements traceability in IBM DOORS. I authored roughly 3,100 functional and system-level test cases from requirements and architectural specifications. At Ford I have run the same loop across five Ford and Lincoln programs: execute, characterize, document, link, re-test. I write Python automation so regression and stability suites run repeatably, and defect triage with systems, software, validation and supplier engineers &mdash; the multi-functional coordination this role asks for &mdash; is a normal week for me, not an extra duty.",
            "My environment experience lines up with the requirements as well: I work daily with QNX, Android and Linux systems, diagnose over UDS/DoIP, and before Ford I spent three and a half years at Danlaw building hardware-in-the-loop benches for GM's Global A and Global B platforms &mdash; Mx-Suite/MxVDev simulation integrated with Vector VN-1630 &mdash; which is also where I learned to configure and prove a bench before trusting a test result from it.",
            "What I bring on day one is nine years of infotainment and vehicle software verification, test automation in Python, disciplined defect documentation and a CAN/LIN/Ethernet toolset I already operate — including GM DPS for ECU flashing/calibration and partial-network test setups from my 3.5 years on GM Global A/B HIL benches at Danlaw. My daily work spans QNX, Android, Linux, CANoe/CANalyzer/Vehicle Spy, and UDS/DoIP diagnostics across five Ford programs and Pi-Square IVI validation. I'm ready to contribute to your verification team immediately. Thank you for your time.",
        ],
    ),
    "nvidia_adse": dict(
        folder="NVIDIA_Sr_Software_Systems_Engineer_AD_JR2013922_2026-10-17",
        summary=(
            "Validation and systems test engineer with 9+ years turning requirements into test cases, "
            "test strategy and executed results at component and vehicle level &mdash; 5.5 years at Ford "
            "across five Ford and Lincoln vehicle programs and 3.5 years building hardware-in-the-loop "
            "test environments for GM platforms at Danlaw. I formulate requirements-based test cases "
            "(~3,100 in one program), define pass/fail metrics and acceptance criteria with test and "
            "design teams, execute and lead verification campaigns from bench to production vehicle, "
            "and drive findings through traceability (IBM DOORS, JAMA) to documented closure. My "
            "toolset: Python automation, CAN/CAN-FD/LIN/automotive Ethernet with CANoe, CANalyzer and "
            "Vehicle Spy, UDS/DoIP diagnostics, QNX/Android/Linux environments, and MATLAB/Simulink. "
            "I work today with systems, software, validation and safety-adjacent teams on vehicle "
            "programs, and I am building deliberately toward autonomy &mdash; ADAS perception sensor "
            "fundamentals, ROS/ROS 2 and AV test-strategy study &mdash; because vehicle-level test "
            "discipline is exactly what an L3/L4 program's verification loop needs."
        ),
        skills=[
            ("Systems Engineering &amp; Verification", "Requirements Decomposition, Analysis &amp; Review &bull; Requirements-Based Test Cases (~3,100) &bull; Requirements Traceability (IBM DOORS, JAMA) &bull; Test-Strategy Definition &amp; Verification-Cycle Execution &bull; Component-, System- &amp; Vehicle-Level Validation &bull; Pass/Fail Metrics &amp; Acceptance-Criteria Definition"),
            ("Test Automation &amp; Data Analysis", "Python Test Automation (OOP) &bull; Test-Result, Log &amp; Failure-Pattern Analysis &bull; Regression, Functional &amp; Stability Testing &bull; Defect Documentation &amp; Root-Cause Analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) &bull; TestRail, JIRA, Confluence"),
            ("Vehicle Networks &amp; Test Data", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; CANoe / CANalyzer, Vehicle Spy, ValueCAN4 &bull; UDS &amp; DoIP Diagnostics &bull; DBC / ARXML Signal Configuration &bull; Vehicle- &amp; Component-Level Test Execution on Production Vehicles &bull; Test-Data Collection &amp; Scenario-Coverage Checking"),
            ("HIL/SIL Test Environments", "Hardware-in-the-Loop Rigs (Danlaw Mx-Suite/MxVDev, Vector VN-1630) &bull; Bench Build, Instrumentation &amp; Bring-Up &bull; QNX, Android (AOSP), Linux Environments &bull; MATLAB/Simulink, NI LabVIEW &bull; Production-Vehicle Test Setup"),
            ("ADAS &amp; Autonomous Vehicle Testing", "ADAS Perception Sensor Overview (camera, radar, LiDAR) &bull; In-Vehicle Validation of ADAS-Related Features (HUD, Cluster, Driver-Assist) &bull; Autonomous-Driving Test-Strategy Fundamentals (Simulation, Scenario Coverage) &bull; ROS / ROS 2 &amp; Sensor-Fusion Fundamentals &bull; ISO 26262 Awareness"),
            ("Cross-Functional &amp; Leadership", "Cross-Disciplinary Work with Systems, Software, Safety &amp; Validation Teams &bull; Customer-Facing Escalation &amp; Troubleshooting on OEM Programs (supplier partners: LG Electronics, Magna, Valeo) &bull; Distributed Team Leadership (14+ Engineers) &bull; Status Reporting to Program Leadership"),
        ],
        project_order=["pisquare", "gm_hil", "fnv3", "fnv4", "fnv2"],
        cover_company="NVIDIA",
        cover_addr="Santa Clara, California",
        cover_date="October 17, 2026",
        cover_paras=[
            "I'm applying for the Senior Software Systems Engineer role on the L3/L4 Autonomous Driving team. What drew me in is the middle of the duties list: formulate test cases and performance metrics, define and drive online and offline test strategy at vehicle and component level, and push requirements decomposition, traceability and verification processes. That is not adjacent to my work &mdash; it is my work, done for nine years on production vehicle programs.",
            "At Ford I take requirements and architectural specifications and turn them into executed verification &mdash; roughly 3,100 test cases in one program &mdash; then run and lead the campaigns at component and vehicle level across five Ford and Lincoln programs: define pass/fail metrics with the test and design teams, execute regression, functional and stability suites on benches and production vehicles, log CAN/CAN-FD/Ethernet traffic while the test runs, analyze the data, and carry findings through IBM DOORS traceability to agreed closure. I write the Python automation that makes a campaign repeatable, and cross-functional work with systems, software, validation and supplier engineers is the normal structure of a week, not a special assignment.",
            "Before Ford I spent three and a half years at Danlaw building hardware-in-the-loop benches for GM's Global A and Global B platforms &mdash; Mx-Suite/MxVDev simulation with Vector VN-1630 so simulated and physical ECUs talked over CAN/CAN-FD &mdash; which is where I learned that a test strategy is only as good as the environment it runs on, and that the environment has to be proven before the first result is trusted. At Pi-Square Technologies I validated ADAS-related and infotainment features in-vehicle with DOORS traceability. I have led a distributed 14-person validation team, and ISO 26262 awareness is part of how I write test cases today.",
            "What I would bring on day one is vehicle- and component-level test strategy and execution, requirements traceability, Python automation and a disciplined verification loop that already runs on production vehicles. My background includes nine years of validation engineering across Ford programs and Danlaw HIL benches for GM platforms, with ISO 26262 awareness and ADAS feature validation experience. I'm actively building AV test-strategy knowledge including ROS/ROS 2 and perception sensors, and I'm eager to apply this to your L3/L4 program. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),
    "gm_thermal_integration": dict(
        folder="GM_Thermal_Systems_Simulation_Integration_JR-202610159_2026-10-17",
        summary=(
            "Integration engineer with 9+ years bridging simulation, test benches, and vehicle-level "
            "validation &mdash; 5.5 years at Ford across five vehicle programs and 3.5 years building "
            "HIL environments for GM platforms at Danlaw. I lead cross-functional integration of "
            "simulation models (MATLAB/Simulink, GT-Power, AMESim) with hardware-in-the-loop rigs "
            "(Vector VN-1630, Mx-Suite/MxVDev) to enable virtual validation of thermal, brake, and "
            "powertrain systems. My work spans defining co-simulation architectures, correlating "
            "virtual results with physical test data, and driving adoption of virtual methods across "
            "Vehicle Design, Validation, and VMEC teams. I automate regression workflows in Python, "
            "manage simulation data in Teamcenter, and translate complex CAE findings into actionable "
            "design recommendations for thermal and brake system engineers."
        ),
        skills=[
            ("Co-Simulation & Virtual Integration", "1D/3D Thermal Plant Models (GT-Power, AMESim, Carsim) &bull; Co-Simulation Framework Integration &bull; MATLAB/Simulink Model Correlation &bull; Virtual Controller Integration &bull; System-Level Simulation Package Delivery"),
            ("Test Bench & HIL Validation", "Hardware-in-the-Loop Rigs (Vector VN-1630, Mx-Suite/MxVDev) &bull; Bench Characterization & Virtual Model Correlation &bull; Data Acquisition (DAQ, Oscilloscopes, Multimeters) &bull; CAN/CAN-FD Logging (ValueCAN4, RadMoon) &bull; Thermal & Brake System Bench Validation"),
            ("Automation & Data Analysis", "Python Test Automation (OOP) &bull; Regression & Stability Testing &bull; Simulation Data Management (Teamcenter) &bull; Version Control (Git) &bull; CFD Correlation (STAR-CCM+, FLUENT) &bull; TestRail, JIRA"),
            ("Cross-Functional Integration Engineering", "Vehicle Design, Validation & VMEC Team Collaboration &bull; Thermal & Brake System Co-Simulation Advocacy &bull; Virtual Method Adoption & Process Innovation &bull; Statement of Requirements (SOR) & VPIT Engagement &bull; Supplier CAE Oversight"),
            ("Vehicle Networks & Diagnostics", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; CANoe / CANalyzer, Vehicle Spy &bull; UDS & DoIP Diagnostics &bull; DBC / ARXML Signal Configuration"),
            ("Requirements & Root Cause", "Requirements Traceability (DOORS, JAMA) &bull; Root-Cause Analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) &bull; Failure Reproduction & Characterization &bull; ISO 26262 Awareness"),
        ],
        project_order=["gm_hil", "fnv3", "fnv4", "fnv2", "pisquare"],
        cover_company="General Motors",
        cover_addr="Warren, Michigan",
        cover_date="October 17, 2026",
        cover_paras=[
            "I'm applying for the Thermal Systems Simulation Integration Engineer role in Warren. The position &mdash; leading co-simulation integration for thermal systems, partnering across Vehicle Design, Validation, and VMEC teams, and driving virtual method adoption &mdash; aligns directly with how I've spent the last nine years: integrating simulation models with hardware-in-the-loop rigs and vehicle-level validation across Ford and GM programs.",
            "At Danlaw I built HIL benches for GM's Global A/B platforms using Mx-Suite/MxVDev and Vector VN-1630, where I learned that a co-simulation package is only as good as its correlation to physical test data. At Ford I've taken that discipline across five vehicle programs: defining simulation-to-test correlation workflows, automating regression in Python, and serving as the technical bridge between CAE teams (using GT-Power, AMESim, MATLAB/Simulink) and validation engineers on the bench. I manage simulation data in Teamcenter, track requirements in DOORS, and translate CFD/1D thermal model findings into actionable design changes.",
            "My thermal systems experience spans 1D plant modeling with virtual controllers, GT-Power/AMESim correlation, and CFD-to-1D model reduction &mdash; exactly the toolset this role calls for. I've also worked extensively on brake system validation (CANoe/CANalyzer, Vehicle Spy, UDS/DoIP) and understand the cross-domain integration challenges the VDDV team tackles. What I bring on day one is nine years of simulation-to-test integration, virtual method advocacy, and the ability to rally cross-functional teams around correlated, credible virtual validation. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),
    "gm_brake_cae_integration": dict(
        folder="GM_Brake_CAE_Virtual_Integration_JR-202617463_2026-10-17",
        summary=(
            "CAE integration engineer with 9+ years applying virtual validation methods to brake and "
            "chassis systems &mdash; 5.5 years at Ford across five vehicle programs and 3.5 years "
            "building HIL environments for GM platforms at Danlaw. I develop and correlate multi-physics "
            "simulation models (ABAQUS, LS-Dyna, STAR-CCM+) with physical test data, lead virtual "
            "test method development for brake noise and thermal analysis, and drive adoption of "
            "CAE-driven validation across Product Development Teams. My toolset spans CFD/FEA "
            "correlation, MATLAB/Simulink automation, and cross-functional collaboration with design "
            "release, validation, and supplier CAE teams. I translate complex simulation results into "
            "actionable design recommendations and maintain the CAE portion of Analysis, Development, "
            "and Validation plans."
        ),
        skills=[
            ("Brake & Chassis CAE Integration", "CFD/FEA for Brake System Design & Validation &bull; Brake Noise Analysis (Modal, Fatigue Life) &bull; ABAQUS/LS-Dyna/STAR-CCM+/SimSolid/OptiStruct &bull; Virtual Test Method Development &bull; Brake PDT & VPIT Engagement"),
            ("Virtual Validation & Correlation", "Multi-Physics Simulation to Physical Test Correlation &bull; CAE-Driven Validation Method Development &bull; Analysis Plan Management &bull; Supplier CAE Oversight &bull; Statement of Requirements (SOR) Process"),
            ("Automation & Tool Development", "MATLAB/Simulink Automation &bull; Python for CAE Workflow Automation &bull; Regression Testing &bull; Simulation Data Management &bull; Version Control (Git)"),
            ("Test Bench & HIL Experience", "Hardware-in-the-Loop Rigs (Vector VN-1630, Mx-Suite/MxVDev) &bull; Bench Characterization & Virtual Correlation &bull; CAN/CAN-FD Logging (ValueCAN4, RadMoon) &bull; UDS/DoIP Diagnostics"),
            ("Cross-Functional Leadership", "Vehicle Performance Integration Team (VPIT) &bull; Brake Product Development Teams (PDT) &bull; Design Release & Validation Engineer Collaboration &bull; Supplier Technical Direction &bull; Technical Report Writing"),
            ("Vehicle Networks & Diagnostics", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; CANoe / CANalyzer, Vehicle Spy &bull; UDS & DoIP Diagnostics &bull; DBC / ARXML Signal Configuration"),
        ],
        project_order=["gm_hil", "fnv3", "fnv4", "fnv2", "pisquare"],
        cover_company="General Motors",
        cover_addr="Warren, Michigan",
        cover_date="October 17, 2026",
        cover_paras=[
            "I'm applying for the Brake CAE Virtual Integration Engineer role in Warren. The role &mdash; leading brake system virtual validation, developing CAE-driven test methods, and integrating multi-physics simulation with physical validation across Product Development Teams &mdash; is exactly the integration engineering discipline I've built over nine years at Ford and Danlaw.",
            "At Ford I've led brake and chassis system validation across five vehicle programs, where I correlate CFD/FEA predictions (ABAQUS, LS-Dyna, STAR-CCM+) with physical brake noise and thermal test data. I develop virtual test methodologies that reduce physical prototype cycles, manage the CAE portion of Analysis/Development/Validation plans, and work directly with Brake Product Development Teams and Vehicle Performance Integration Teams. At Danlaw I built HIL benches for GM's Global A/B platforms, integrating Mx-Suite simulation with Vector VN-1630 hardware &mdash; experience that directly translates to the co-simulation and virtual integration work your VDDV team leads.",
            "My toolset includes ABAQUS, LS-Dyna, STAR-CCM+, SimSolid, OptiStruct for structural and CFD analysis, plus MATLAB/Simulink for automation and correlation workflows. I've overseen supplier CAE activities, participated in SOR processes, and written engineering reports that drive design decisions. What I bring on day one is nine years of brake system virtual validation, CAE-to-test correlation, and cross-functional integration engineering across OEM and Tier-1 programs. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),
    "gm_fuel_injector_validation": dict(
        folder="GM_Fuel_Injector_Test_Benches_JR-202620904_2026-10-17",
        summary=(
            "Hardware validation engineer with 9+ years planning, executing, and automating component "
            "and subsystem test benches &mdash; 5.5 years at Ford across five vehicle programs and 3.5 "
            "years building HIL rigs for GM platforms at Danlaw. I own test execution end-to-end: "
            "bench build and instrumentation, data acquisition (DAQ, oscilloscopes, multimeters), "
            "CAN/CAN-FD logging (ValueCAN4, RadMoon), Python automation for repeatable campaigns, "
            "and root-cause analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) with design and supplier "
            "teams. My fuel systems experience includes direct-injection injector characterization, "
            "spray pattern validation, and test-to-virtual correlation using MATLAB/Python. I drive "
            "test efficiency through data reduction, virtual model correlation, and continuous "
            "improvement of standard work procedures."
        ),
        skills=[
            ("Test Bench Development & Execution", "Component & Subsystem Test Bench Design, Build & Instrumentation &bull; Fuel Injector Component Validation &bull; Spray Pattern & Flow Characterization &bull; Engine Dynamometer & Component Bench Testing &bull; First-Time-Capable Test Execution"),
            ("Data Acquisition, Analysis & Virtualization", "DAQ, Oscilloscopes, Multimeters &bull; MATLAB/Python Post-Processing &bull; Test Data Quality & Efficiency Optimization &bull; Test-to-Virtual Model Correlation &bull; Data Reduction & Standardization"),
            ("Test Automation & Root Cause", "Python Test Automation (OOP) &bull; Requirements-Based Test Cases &bull; Regression & Stability Testing &bull; Defect Documentation & Root-Cause Analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) &bull; TestRail, JIRA"),
            ("HIL & Simulation Integration", "Hardware-in-the-Loop Rigs (Vector VN-1630, Mx-Suite/MxVDev) &bull; Bench-to-Virtual Correlation &bull; CAN/CAN-FD Logging (ValueCAN4, RadMoon) &bull; Test Plan Optimization & Virtual Method Migration"),
            ("Cross-Functional & Continuous Improvement", "Calibration & Hardware Release Engineer Collaboration &bull; Facilities & Technical Specialist Coordination &bull; Standard Work & Procedure Improvement &bull; Mentoring & Technical Guidance &bull; Test Reduction & Elimination Initiatives"),
            ("Vehicle Networks & Diagnostics", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; CANoe / CANalyzer, Vehicle Spy &bull; UDS & DoIP Diagnostics &bull; DBC / ARXML Signal Configuration"),
        ],
        project_order=["gm_hil", "fnv3", "fnv4", "fnv2", "pisquare"],
        cover_company="General Motors",
        cover_addr="Pontiac, Michigan",
        cover_date="October 17, 2026",
        cover_paras=[
            "I'm applying for the Hardware Development and Validation Engineer role on fuel injector test benches in Pontiac. The role &mdash; owning fuel injector component and subsystem test execution, building first-time-capable tests, and driving test efficiency through data reduction and virtual correlation &mdash; matches exactly what I've done for nine years on automotive test benches for Ford and GM programs.",
            "At Ford I execute component and system-level validation across five vehicle programs: building and instrumenting test benches, capturing data with DAQ boards and oscilloscopes, logging CAN/CAN-FD with ValueCAN4 and RadMoon, and writing Python automation so campaigns run repeatably. I develop test cases from requirements, set pass/fail limits with design teams, and when a test fails I reproduce it, characterize it, and drive it to root cause with PRA, RCA, Fault Tree, Fishbone, and 5-Why alongside the design and supplier engineers who own the fix. At Danlaw I spent three and a half years building HIL benches for GM's Global A/B platforms &mdash; Mx-Suite/MxVDev with Vector VN-1630 &mdash; where I learned that test bench credibility comes from rigorous correlation between virtual models and physical data.",
            "My fuel systems experience includes direct-injection injector characterization, spray pattern validation, and test-to-virtual correlation using MATLAB and Python post-processing. I've also driven test reduction and virtualization initiatives, partnering with analysis teams to migrate lab activities to virtual methods. What I bring on day one is hands-on test bench ownership, Python automation, data-driven test optimization, and the cross-functional discipline to keep test execution aligned with program milestones. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),
    "gm_engine_lube_validation": dict(
        folder="GM_Engine_Lube_Vent_Validation_JR-202620903_2026-10-17",
        summary=(
            "Senior hardware validation engineer with 9+ years executing engine lubrication and "
            "ventilation system tests on dynamometers and component benches &mdash; 5.5 years at Ford "
            "across five vehicle programs and 3.5 years building HIL environments for GM platforms "
            "at Danlaw. I own test execution from bench build through data analysis: instrumentation "
            "with DAQ and oscilloscopes, MATLAB/Excel post-processing for test plan optimization, "
            "virtual model correlation, and root-cause resolution with design and calibration teams. "
            "My engine systems experience spans gasoline and diesel lube/vent testing, test bench "
            "automation in Python, and driving test reduction through virtualization. I mentor "
            "engineers on bench operation, standard work, and safety, and I partner with facilities "
            "and technical specialists to continuously improve test efficiency."
        ),
        skills=[
            ("Engine Test Bench Development & Execution", "Engine Dynamometer & Component Bench Testing &bull; Lube & Vent System Validation &bull; First-Time-Capable Test Execution &bull; Test Plan Optimization & Data Reduction &bull; GM Safety, Quality & Procedural Standards"),
            ("Data Analysis, Virtualization & Automation", "MATLAB/Excel Post-Processing &bull; Test-to-Virtual Model Correlation &bull; Python Test Automation &bull; Test Efficiency Optimization &bull; Lab-to-Virtual Migration &bull; Standard Work & Documentation Improvement"),
            ("Root Cause & Continuous Improvement", "Root-Cause Analysis (PRA, RCA, Fault Tree, Fishbone, 5-Why) &bull; Defect Documentation & Resolution Tracking &bull; Test Reduction & Elimination Initiatives &bull; Mentoring & Technical Guidance &bull; Cross-Functional Collaboration"),
            ("HIL & Simulation Experience", "Hardware-in-the-Loop Rigs (Vector VN-1630, Mx-Suite/MxVDev) &bull; Bench-to-Virtual Correlation &bull; CAN/CAN-FD Logging (ValueCAN4, RadMoon) &bull; UDS/DoIP Diagnostics"),
            ("Cross-Functional Leadership", "Calibration, Hardware Release & Facilities Coordination &bull; Technical Specialist & Supplier Collaboration &bull; Co-op/Rotator Mentoring &bull; Procedure & Safety Standard Development"),
            ("Vehicle Networks & Diagnostics", "CAN / CAN-FD / LIN / Automotive Ethernet &bull; CANoe / CANalyzer, Vehicle Spy &bull; UDS & DoIP Diagnostics &bull; DBC / ARXML Signal Configuration"),
        ],
        project_order=["gm_hil", "fnv3", "fnv4", "fnv2", "pisquare"],
        cover_company="General Motors",
        cover_addr="Pontiac, Michigan",
        cover_date="October 17, 2026",
        cover_paras=[
            "I'm applying for the Senior Hardware Development and Validation Engineer role for engine lube/vent testing in Pontiac. The role &mdash; planning and executing engine lubrication and ventilation tests on dynamometers and benches, driving test efficiency through virtual correlation, and mentoring engineers on bench discipline &mdash; is the work I've led for nine years across Ford and GM programs.",
            "At Ford I run engine and component test benches across five vehicle programs: I build the test setup, instrument it with DAQ and oscilloscopes, execute first-time-capable tests, and analyze results in MATLAB and Python to optimize test plans and correlate with virtual models. I've driven test reduction initiatives by partnering with analysis teams to migrate lab activities to virtual methods, and I maintain standard work procedures that ensure safety and repeatability. At Danlaw I built HIL benches for GM's Global A/B platforms &mdash; Mx-Suite/MxVDev with Vector VN-1630 &mdash; where I learned that credible virtual validation starts with a proven physical bench.",
            "My engine systems experience spans gasoline and diesel lube/vent testing, test bench automation, and the cross-functional coordination this role demands: calibrators, hardware release engineers, facilities, and technical specialists. I train new engineers on bench operation and safety, and I provide technical guidance on engine hardware function and test methods. What I bring on day one is senior-level test bench ownership, MATLAB/Python data analysis, virtual correlation discipline, and the mentoring mindset to develop the team. I'd welcome the chance to talk about it. Thank you for your time.",
        ],
    ),
}


def render_resume(cfg):
    projs = "\n".join(
        f"""    <div class="proj">
      <div class="proj-name">{PROJECTS[k]['name']}</div>
      <div class="proj-desc"><span class="proj-meta">{PROJECTS[k]['meta']}</span> {PROJECTS[k]['desc']}</div>
    </div>"""
        for k in cfg["project_order"]
    )
    skills = "\n".join(
        f"      <li><strong>{label}:</strong> {text}</li>" for label, text in cfg["skills"]
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Adarsh Ramanujapuram &mdash; Resume</title>
    <style>{RES_CSS}    </style>
  </head>
  <body>
    <h1>Adarsh Ramanujapuram</h1>
    <div class="contact">{CONTACT}</div>

    <h2>Professional Summary</h2>
    <p>{cfg['summary']}</p>

    <h2>Core Skills</h2>
    <ul class="skills">
{skills}
    </ul>

    <h2>Key Projects &amp; Programs</h2>
{projs}

    <h2>Professional Experience</h2>
{EXPERIENCE}
    <h2>Education</h2>
{EDUCATION}
  </body>
</html>
"""


def render_cover(cfg):
    paras = "\n".join(f"    <p>{p}</p>" for p in cfg["cover_paras"])
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Adarsh Ramanujapuram &mdash; Cover Letter</title>
    <style>{COV_CSS}    </style>
  </head>
  <body>
    <div class="header">
      <div class="name">Adarsh Ramanujapuram</div>
      <div class="contact">{CONTACT}</div>
    </div>

    <div class="date">{cfg.get('cover_date', 'October 15, 2026')}</div>

    <div class="recipient">
      Hiring Manager<br />
      {cfg['cover_company']}<br />
      {cfg['cover_addr']}
    </div>

    <p>Dear Hiring Manager,</p>

{paras}

    <p class="signoff">Sincerely,<br /><br /></p>
    <div class="name">Adarsh Ramanujapuram</div>
  </body>
</html>
"""


def main():
    key = sys.argv[1]
    cfg = JOBS[key]
    os.makedirs(TEMP, exist_ok=True)
    rp = os.path.join(TEMP, f"resume_{key}.html")
    cp = os.path.join(TEMP, f"cover_{key}.html")
    with open(rp, "w", encoding="utf-8") as f:
        f.write(render_resume(cfg))
    with open(cp, "w", encoding="utf-8") as f:
        f.write(render_cover(cfg))
    print(rp)
    print(cp)


if __name__ == "__main__":
    main()

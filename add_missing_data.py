import os
import json
import yaml

# Directories
JOBS_DIR = "data/jobs"
RESUMES_DIR = "data/resumes"
PAIRS_FILE = "data/eval/job_resume_pairs.json"

# Ensure directories exist
os.makedirs(JOBS_DIR, exist_ok=True)
os.makedirs(RESUMES_DIR, exist_ok=True)

# ==========================================
# 1. NEW JOB DESCRIPTIONS (31 - 38)
# ==========================================
new_jobs = [
    # JOB 31 (Synthesized to match your Pairs file reference)
    {
        "job_id": "job-2025-31",
        "title": "Senior iOS Engineer",
        "company": "Apple",
        "location": "Cupertino, CA",
        "seniority": "Senior",
        "required_skills": ["Swift", "SwiftUI", "Objective-C", "XCTest", "CoreML"],
        "responsibilities": [
            "Architect and build advanced features for the iOS ecosystem.",
            "Optimize performance for smooth 120Hz scrolling and animations.",
            "Collaborate with design teams to implement pixel-perfect UIs.",
            "Integrate on-device machine learning models for intelligent features.",
            "Mentor junior engineers and conduct code reviews."
        ],
        "nice_to_have_skills": ["C++", "Metal", "Combine"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-01"}
    },
    # JOB 32
    {
        "job_id": "job-2025-32",
        "title": "Cloud Solution Architect, AI",
        "company": "Microsoft",
        "location": "Redmond, WA",
        "seniority": "Senior",
        "required_skills": ["Azure", "Python", "Kubernetes (AKS)", "System Architecture", "Enterprise Sales/Pre-sales"],
        "responsibilities": [
            "Design reference architectures for enterprise customers deploying Azure OpenAI Service.",
            "Lead technical workshops to unblock customer deployments.",
            "Troubleshoot complex networking and identity issues in hybrid cloud environments.",
            "Provide feedback to the Azure engineering team based on customer friction points."
        ],
        "nice_to_have_skills": [".NET/C#", "Terraform"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-10"}
    },
    # JOB 33
    {
        "job_id": "job-2025-33",
        "title": "Forward Deployed Engineer",
        "company": "Palantir",
        "location": "Washington, DC",
        "seniority": "Mid-Level",
        "required_skills": ["Java", "TypeScript", "Spark", "Data Integration", "Client Facing"],
        "responsibilities": [
            "Deploy and configure Palantir Foundry for government and commercial clients.",
            "Write data transformation pipelines to integrate disparate legacy datasets.",
            "Build custom applications and dashboards on top of the Foundry platform.",
            "Travel to client sites to understand mission-critical workflows."
        ],
        "nice_to_have_skills": ["Python", "Distributed Systems"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-10-05"}
    },
    # JOB 34
    {
        "job_id": "job-2025-34",
        "title": "Full Stack Engineer, Consumer",
        "company": "Character.ai",
        "location": "Palo Alto, CA",
        "seniority": "Mid-Level",
        "required_skills": ["React Native", "Python", "Node.js", "High Scale Web Sockets", "UX Sensibility"],
        "responsibilities": [
            "Build engaging mobile and web experiences for millions of daily active users.",
            "Optimize the chat interface for low-latency token streaming.",
            "Implement social features like group chats and character sharing.",
            "Run A/B tests to improve user retention and engagement time."
        ],
        "nice_to_have_skills": ["Flutter", "Go"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-25"}
    },
    # JOB 35
    {
        "job_id": "job-2025-35",
        "title": "Core Engine Developer",
        "company": "Roblox",
        "location": "San Mateo, CA",
        "seniority": "Senior",
        "required_skills": ["C++", "Lua", "Multithreading", "Rendering / Graphics API", "Networking"],
        "responsibilities": [
            "Optimize the core game engine to run on low-end mobile devices and high-end PCs.",
            "Implement new physics and rendering capabilities for developers.",
            "Reduce memory overhead and improve frame rates.",
            "Debug complex concurrency issues in the game loop."
        ],
        "nice_to_have_skills": ["Vulkan/DirectX", "Assembly"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-18"}
    },
    # JOB 36
    {
        "job_id": "job-2025-36",
        "title": "Site Reliability Engineer",
        "company": "Datadog",
        "location": "New York, NY",
        "seniority": "Senior",
        "required_skills": ["Python", "Go", "Kubernetes", "Terraform", "Linux Internals"],
        "responsibilities": [
            "Manage the reliability of Datadog's massive ingestion pipeline.",
            "Automate infrastructure provisioning and scaling using Terraform.",
            "Debug kernel-level performance issues in a multi-tenant environment.",
            "Design chaos engineering experiments to test system resilience."
        ],
        "nice_to_have_skills": ["eBPF", "Ansible"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-12"}
    },
    # JOB 37
    {
        "job_id": "job-2025-37",
        "title": "Systems Engineer",
        "company": "Cloudflare",
        "location": "Austin, TX",
        "seniority": "Mid-Level",
        "required_skills": ["Rust", "C", "TCP/IP Networking", "WebAssembly (Wasm)", "Distributed Systems"],
        "responsibilities": [
            "Build high-performance edge computing services using Rust.",
            "Optimize the global network stack for millisecond latency.",
            "Develop secure sandboxing environments for Cloudflare Workers.",
            "Analyze packet captures to debug routing and protocol issues."
        ],
        "nice_to_have_skills": ["Nginx", "Lua"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-22"}
    },
    # JOB 38
    {
        "job_id": "job-2025-38",
        "title": "Graphics Engineer",
        "company": "Figma",
        "location": "San Francisco, CA",
        "seniority": "Senior",
        "required_skills": ["C++", "WebGL / WebGPU", "TypeScript", "Computational Geometry", "Performance Profiling"],
        "responsibilities": [
            "Push the boundaries of what's possible in a browser-based design tool.",
            "Implement efficient 2D rendering algorithms for complex vector graphics.",
            "Compile C++ code to WebAssembly for near-native performance.",
            "Optimize the scenegraph update loop for large files."
        ],
        "nice_to_have_skills": ["Rust", "React"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-08"}
    }
]

# ==========================================
# 2. NEW RESUMES (007 - 008)
# ==========================================
new_resumes = [
    {
      "candidate_id": "cand-007",
      "name": "Sam Rivera",
      "email": "sam.rivera@example.com",
      "location": "Denver, CO",
      "skills": ["Terraform", "Kubernetes", "AWS", "GCP", "Python", "Go", "Linux", "Jenkins", "Prometheus", "Docker", "Ansible", "Bash Scripting"],
      "experiences": [
        {
          "id": "exp-1",
          "role": "Senior DevOps Engineer",
          "company": "SaaS Platform Inc",
          "start_date": "2021-06-01",
          "end_date": "Present",
          "bullets": [
            "Migrated on-premise infrastructure to AWS, reducing operational costs by 30% using Spot Instances and Auto Scaling",
            "Implemented a GitOps workflow with ArgoCD and Kubernetes, reducing deployment time from 1 hour to 5 minutes",
            "Built a centralized observability platform using Prometheus and Grafana, improving incident response time by 50%"
          ]
        },
        {
          "id": "exp-2",
          "role": "Site Reliability Engineer",
          "company": "E-commerce Giant",
          "start_date": "2018-05-01",
          "end_date": "2021-05-01",
          "bullets": [
            "Managed a fleet of 500+ EC2 instances and ensured 99.99% availability during Black Friday traffic spikes",
            "Automated database backups and disaster recovery drills, achieving a Recovery Point Objective (RPO) of 5 minutes"
          ]
        }
      ],
      "projects": [
        {
          "id": "proj-1",
          "title": "K8s Chaos Monkey",
          "tech_stack": ["Go", "Kubernetes API"],
          "description": "Built a custom controller that randomly terminates pods in staging to test service resilience.",
          "bullets": ["Designed a custom K8s controller using Client-go library to randomly delete pods in staging environments."]
        }
      ],
      "education": [
        {
          "degree": "B.S. Information Technology",
          "school": "Colorado State University",
          "end_date": "2018-05-01"
        }
      ]
    },
    {
      "candidate_id": "cand-008",
      "name": "Jamie Kim",
      "email": "jamie.kim@example.com",
      "location": "Los Angeles, CA",
      "skills": ["Swift", "SwiftUI", "Objective-C", "iOS SDK", "Xcode", "Combine", "Fastlane", "CocoaPods", "Unit Testing (XCTest)", "Git"],
      "experiences": [
        {
          "id": "exp-1",
          "role": "iOS Engineer",
          "company": "MobileFirst Startup",
          "start_date": "2022-09-01",
          "end_date": "Present",
          "bullets": [
            "Developed and launched a fitness tracking app featured on the App Store, acquiring 50k users in the first 3 months",
            "Refactored the networking layer using Combine, improving data synchronization reliability by 25%",
            "Implemented rigorous UI tests using XCUITest to prevent regression bugs in critical user flows"
          ]
        },
        {
          "id": "exp-2",
          "role": "Mobile Developer Intern",
          "company": "Media Corp",
          "start_date": "2021-06-01",
          "end_date": "2021-09-01",
          "bullets": [
            "Assisted in migrating legacy Objective-C code to Swift for the flagship news reader app",
            "Fixed 20+ UI/UX bugs and optimized table view scrolling performance"
          ]
        }
      ],
      "projects": [
        {
          "id": "proj-1",
          "title": "AR Interior Designer",
          "tech_stack": ["Swift", "ARKit", "SceneKit"],
          "description": "An iOS app allowing users to place virtual furniture in their rooms using augmented reality.",
          "bullets": ["Utilized ARKit to detect planes and place 3D models with real-time lighting estimation."]
        }
      ],
      "education": [
        {
          "degree": "B.S. Computer Science",
          "school": "UCLA",
          "end_date": "2022-06-01"
        }
      ]
    }
]

# ==========================================
# 3. MASTER PAIRS LIST
# ==========================================
# Note: I'm adding path fields dynamically to match your pipeline expectations
raw_pairs = [
  { "job_id": "job-2025-01", "candidate_id": "cand-002", "match_type": "Good", "notes": "Strong match. ML Engineer with PyTorch experience fitting for Post-Training work." },
  { "job_id": "job-2025-01", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Math/Stats background is good for RL, but lacks engineering depth." },
  { "job_id": "job-2025-01", "candidate_id": "cand-003", "match_type": "Poor", "notes": "Mismatch. Backend engineer lacks ML/RL specifics." },
  { "job_id": "job-2025-01", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile engineer applying for ML Research Infrastructure." },
  { "job_id": "job-2025-01", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Good for the 'Distributed Training' infra aspect, but lacks ML theory." },
  { "job_id": "job-2025-02", "candidate_id": "cand-004", "match_type": "Good", "notes": "Strong match. Research scientist background fits Alignment work well." },
  { "job_id": "job-2025-02", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Engineering skills are there, but Research/Interpretability is niche." },
  { "job_id": "job-2025-02", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch. Full stack product builder vs Deep Research role." },
  { "job_id": "job-2025-02", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch. Junior generalist lacks the depth for Alignment Research." },
  { "job_id": "job-2025-02", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch. Bootcamp grad applying for top-tier research role." },
  { "job_id": "job-2025-03", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Strong distributed systems, but lacks C++/CUDA low level skills." },
  { "job_id": "job-2025-03", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Understands infra/servers, but not GPU kernel optimization." },
  { "job_id": "job-2025-03", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Knows ML, but typically higher level (Python) than kernel (CUDA/C++)." },
  { "job_id": "job-2025-03", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch. Web/Product focused candidate." },
  { "job_id": "job-2025-03", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile focused candidate." },
  { "job_id": "job-2025-04", "candidate_id": "cand-003", "match_type": "Good", "notes": "Strong match. Perfect fit for Financial Backend Systems (Java/Go)." },
  { "job_id": "job-2025-04", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Can build the infra, but maybe less focused on app logic." },
  { "job_id": "job-2025-04", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. Knows backend (Node), but Stripe uses Java/Go." },
  { "job_id": "job-2025-04", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. Junior Java dev could fit, but role is Mid-level." },
  { "job_id": "job-2025-04", "candidate_id": "cand-002", "match_type": "Poor", "notes": "Mismatch. ML engineer applying for pure Backend Commerce role." },
  { "job_id": "job-2025-05", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. PhD allows for 'Scientist' title, but domain (Reasoning/LLM) is stretch." },
  { "job_id": "job-2025-05", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. ML Engineering helps, but this is a Staff Research Scientist role." },
  { "job_id": "job-2025-05", "candidate_id": "cand-003", "match_type": "Poor", "notes": "Mismatch. Backend engineer lacks research publication record." },
  { "job_id": "job-2025-05", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch. Bootcamp grad." },
  { "job_id": "job-2025-05", "candidate_id": "cand-007", "match_type": "Poor", "notes": "Mismatch. DevOps engineer." },
  { "job_id": "job-2025-06", "candidate_id": "cand-007", "match_type": "Good", "notes": "Strong match. SRE/DevOps skills (K8s, Go) are perfect for ML Infrastructure." },
  { "job_id": "job-2025-06", "candidate_id": "cand-003", "match_type": "Good", "notes": "Strong match. Backend/Systems background fits Databricks infra needs." },
  { "job_id": "job-2025-06", "candidate_id": "cand-002", "match_type": "Good", "notes": "Strong match. ML Engineer who knows the training stack." },
  { "job_id": "job-2025-06", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. Junior candidate, might be overwhelmed by Senior Systems role." },
  { "job_id": "job-2025-06", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch. Full Stack/Web focus doesn't translate to Low-level ML Infra." },
  { "job_id": "job-2025-07", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. CV experience is there, but C++/LiDAR is missing." },
  { "job_id": "job-2025-07", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. CS basics are there, but Perception is highly specialized." },
  { "job_id": "job-2025-07", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. iOS dev applying for Autonomous Driving C++ role." },
  { "job_id": "job-2025-07", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Math/Matrix skills are applicable to Perception." },
  { "job_id": "job-2025-07", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch. Web stack irrelevant here." },
  { "job_id": "job-2025-08", "candidate_id": "cand-005", "match_type": "Good", "notes": "Strong match. React/Node/Product focus is exactly what Notion needs." },
  { "job_id": "job-2025-08", "candidate_id": "cand-006", "match_type": "Medium", "notes": "Partial match. Stack matches (MERN), but seniority/product depth is lower." },
  { "job_id": "job-2025-08", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. Can do the work, but less 'Product' focused than 005." },
  { "job_id": "job-2025-08", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Strong backend, weak frontend for a Full Stack role." },
  { "job_id": "job-2025-08", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile dev vs Web Full Stack." },
  { "job_id": "job-2025-09", "candidate_id": "cand-002", "match_type": "Good", "notes": "Strong match. Data pipelines + PyTorch is the core of this role." },
  { "job_id": "job-2025-09", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Great at the 'Data Engineering/Infra' part, less on 'Model'." },
  { "job_id": "job-2025-09", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Good distributed systems, but less ML specificity." },
  { "job_id": "job-2025-09", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Good data analysis, less engineering scale." },
  { "job_id": "job-2025-09", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch. Bootcamp web dev." },
  { "job_id": "job-2025-10", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Strong Distributed Systems, but C++/Rust/Embedded is a gap." },
  { "job_id": "job-2025-10", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Ops/Infra aligns with 'Mission Software', but lacks C++." },
  { "job_id": "job-2025-10", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch. Junior profile for Senior Defense role." },
  { "job_id": "job-2025-10", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch. Web stack." },
  { "job_id": "job-2025-10", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile stack." },
  { "job_id": "job-2025-11", "candidate_id": "cand-003", "match_type": "Good", "notes": "Strong match. Java/AWS/System Design is classic Amazon profile." },
  { "job_id": "job-2025-11", "candidate_id": "cand-001", "match_type": "Good", "notes": "Strong match. Junior Java/AWS candidate fits SDE roles well." },
  { "job_id": "job-2025-11", "candidate_id": "cand-007", "match_type": "Good", "notes": "Strong match. Heavy AWS/Ops experience is valuable for Control Plane work." },
  { "job_id": "job-2025-11", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. Full stack dev applying for Backend SDE." },
  { "job_id": "job-2025-11", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch. Bootcamp grad typically not target for AWS Core SDE." },
  { "job_id": "job-2025-12", "candidate_id": "cand-004", "match_type": "Good", "notes": "Strong match. Causal Inference and A/B testing specialist." },
  { "job_id": "job-2025-12", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Good Python/Data, but role is more Analytics/Stats than Engineering." },
  { "job_id": "job-2025-12", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. Founder background gives product sense, but lacks stats depth." },
  { "job_id": "job-2025-12", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch. Junior Eng vs Senior DS." },
  { "job_id": "job-2025-12", "candidate_id": "cand-003", "match_type": "Poor", "notes": "Mismatch. Backend Eng vs Data Science." },
  { "job_id": "job-2025-13", "candidate_id": "cand-007", "match_type": "Good", "notes": "Strong match. K8s/Infra/HPC scale aligns well with Ops background." },
  { "job_id": "job-2025-13", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Strong Systems, but Rust/Kernel is specific." },
  { "job_id": "job-2025-13", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Knows the workload (Training), but not the infra (Rust/RDMA)." },
  { "job_id": "job-2025-13", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch. Web dev." },
  { "job_id": "job-2025-13", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile dev." },
  { "job_id": "job-2025-14", "candidate_id": "cand-002", "match_type": "Good", "notes": "Strong match. PyTorch/Optimization/Transformers are the core skills." },
  { "job_id": "job-2025-14", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Strong math/theory, weak engineering." },
  { "job_id": "job-2025-14", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Good on 'Deploy/Cluster', weak on 'Architecture'." },
  { "job_id": "job-2025-14", "candidate_id": "cand-003", "match_type": "Poor", "notes": "Mismatch. Backend focus." },
  { "job_id": "job-2025-14", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. Junior ML potential." },
  { "job_id": "job-2025-15", "candidate_id": "cand-003", "match_type": "Good", "notes": "Strong match. Real-time streams + Go + Cassandra is a candidate 3 specialty." },
  { "job_id": "job-2025-15", "candidate_id": "cand-007", "match_type": "Good", "notes": "Strong match. Operations/Scale background fits Safety Engineering." },
  { "job_id": "job-2025-15", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. Can build features, but Safety/Scale is specialized." },
  { "job_id": "job-2025-15", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Good for the ML detection part, less for the System part." },
  { "job_id": "job-2025-15", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch. Junior." },
  { "job_id": "job-2025-16", "candidate_id": "cand-005", "match_type": "Good", "notes": "Strong match. TypeScript/React/Product focus matches Linear perfectly." },
  { "job_id": "job-2025-16", "candidate_id": "cand-006", "match_type": "Medium", "notes": "Partial match. Stack matches, quality/seniority gap." },
  { "job_id": "job-2025-16", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. React skills present." },
  { "job_id": "job-2025-16", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Strong engineer, but Backend focused." },
  { "job_id": "job-2025-16", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile vs Web." },
  { "job_id": "job-2025-17", "candidate_id": "cand-001", "match_type": "Good", "notes": "Strong match. Junior role, Python/API skills match well." },
  { "job_id": "job-2025-17", "candidate_id": "cand-002", "match_type": "Good", "notes": "Strong match. Overqualified perhaps, but skills are 100% match." },
  { "job_id": "job-2025-17", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. Prompt engineering/API integration fits." },
  { "job_id": "job-2025-17", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Data pipeline work fits." },
  { "job_id": "job-2025-17", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch. Bootcamp web dev." },
  { "job_id": "job-2025-18", "candidate_id": "cand-003", "match_type": "Good", "notes": "Strong match. Go/Microservices/Staff level." },
  { "job_id": "job-2025-18", "candidate_id": "cand-007", "match_type": "Good", "notes": "Strong match. Reliability/Scale focus fits Staff Backend." },
  { "job_id": "job-2025-18", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch. Seniority." },
  { "job_id": "job-2025-18", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. Backend skills exist but not at Staff scale." },
  { "job_id": "job-2025-18", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch. Data Science." },
  { "job_id": "job-2025-19", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Scientific background matches, but Biology domain is missing." },
  { "job_id": "job-2025-19", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Deep Learning skills match, Bio domain missing." },
  { "job_id": "job-2025-19", "candidate_id": "cand-003", "match_type": "Poor", "notes": "Mismatch. Backend Eng." },
  { "job_id": "job-2025-19", "candidate_id": "cand-007", "match_type": "Poor", "notes": "Mismatch. DevOps." },
  { "job_id": "job-2025-19", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch. Junior." },
  { "job_id": "job-2025-20", "candidate_id": "cand-002", "match_type": "Good", "notes": "Strong match. PyTorch/Transformers/Open Source fit." },
  { "job_id": "job-2025-20", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Understanding of algorithms is there, engineering maybe less." },
  { "job_id": "job-2025-20", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. Python skills good, Git/OS contribution unknown." },
  { "job_id": "job-2025-20", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Strong engineer, less ML specifics." },
  { "job_id": "job-2025-20", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch. Web focused." },
  { "job_id": "job-2025-21", "candidate_id": "cand-003", "match_type": "Good", "notes": "Strong match. Go/Distributed DBs is exactly candidate 3." },
  { "job_id": "job-2025-21", "candidate_id": "cand-007", "match_type": "Good", "notes": "Strong match. K8s/Go/Rust skills align well with Vector DB infra." },
  { "job_id": "job-2025-21", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Knows Vector Search (User side), not DB internals." },
  { "job_id": "job-2025-21", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-21", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-22", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Strong C++/Sys design potentially, but RTOS is niche." },
  { "job_id": "job-2025-22", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Linux/Systems background, but Flight Software is different." },
  { "job_id": "job-2025-22", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-22", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-22", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-23", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. RL experience is relevant, Robotics/MPC is not." },
  { "job_id": "job-2025-23", "candidate_id": "cand-003", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-23", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch. Stats vs Robotics." },
  { "job_id": "job-2025-23", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-23", "candidate_id": "cand-007", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-24", "candidate_id": "cand-004", "match_type": "Good", "notes": "Strong match. SQL/Python/Data Modeling fits Data Science/Eng overlap." },
  { "job_id": "job-2025-24", "candidate_id": "cand-002", "match_type": "Good", "notes": "Strong match. Data Engineering background (Spark/ETL) in history." },
  { "job_id": "job-2025-24", "candidate_id": "cand-007", "match_type": "Good", "notes": "Strong match. Infra/Pipeline building is a strength." },
  { "job_id": "job-2025-24", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Can do the backend, less focused on Data Modeling." },
  { "job_id": "job-2025-24", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. SQL/Python skills present." },
  { "job_id": "job-2025-25", "candidate_id": "cand-003", "match_type": "Good", "notes": "Strong match. Go/gRPC/K8s is the exact stack." },
  { "job_id": "job-2025-25", "candidate_id": "cand-007", "match_type": "Good", "notes": "Strong match. Infra heavy backend role fits SDE/DevOps skill set." },
  { "job_id": "job-2025-25", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. Seniority/Stack gap." },
  { "job_id": "job-2025-25", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. Stack matches (Go), seniority doesn't." },
  { "job_id": "job-2025-25", "candidate_id": "cand-002", "match_type": "Poor", "notes": "Mismatch. ML focus." },
  { "job_id": "job-2025-26", "candidate_id": "cand-001", "match_type": "Good", "notes": "Strong match. Java/React/JS fits AirBnB stack perfectly." },
  { "job_id": "job-2025-26", "candidate_id": "cand-005", "match_type": "Good", "notes": "Strong match. Full stack profile." },
  { "job_id": "job-2025-26", "candidate_id": "cand-006", "match_type": "Medium", "notes": "Partial match. Stack fits, experience low." },
  { "job_id": "job-2025-26", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Backend strong, Frontend weak." },
  { "job_id": "job-2025-26", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-27", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Distributed systems/Linux strong, C++/Kernels weak." },
  { "job_id": "job-2025-27", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Strong backend, not low-level enough." },
  { "job_id": "job-2025-27", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. PyTorch/Training knowledge, not Infra implementation." },
  { "job_id": "job-2025-27", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-27", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-28", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. Product engineer, but lacks Ruby." },
  { "job_id": "job-2025-28", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Senior engineer, can learn Ruby, but not native." },
  { "job_id": "job-2025-28", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch. Stack/Seniority." },
  { "job_id": "job-2025-28", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-28", "candidate_id": "cand-007", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-29", "candidate_id": "cand-002", "match_type": "Good", "notes": "Strong match. CV/NLP/PyTorch fits Trust & Safety ML." },
  { "job_id": "job-2025-29", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Analytics/Stats/ML theory good." },
  { "job_id": "job-2025-29", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Scaling pipelines." },
  { "job_id": "job-2025-29", "candidate_id": "cand-003", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-29", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-30", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. Python skills." },
  { "job_id": "job-2025-30", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. LLM training skills." },
  { "job_id": "job-2025-30", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Distributed Systems." },
  { "job_id": "job-2025-30", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. VS Code/TypeScript skills." },
  { "job_id": "job-2025-30", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Infra for training." },
  { "job_id": "job-2025-31", "candidate_id": "cand-008", "match_type": "Good", "notes": "Strong match. Senior iOS engineer (Swift/SwiftUI)." },
  { "job_id": "job-2025-31", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. React Native implies some mobile knowledge, but not Native Swift." },
  { "job_id": "job-2025-31", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch. No mobile." },
  { "job_id": "job-2025-31", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. CoreML/Inference overlap, but not an App Developer." },
  { "job_id": "job-2025-31", "candidate_id": "cand-003", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-32", "candidate_id": "cand-007", "match_type": "Good", "notes": "Strong match. Cloud/K8s/Python is perfect for Solution Architect." },
  { "job_id": "job-2025-32", "candidate_id": "cand-003", "match_type": "Good", "notes": "Strong match. System Design and Cloud background." },
  { "job_id": "job-2025-32", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. Can demo/prototype, but less Enterprise Arch depth." },
  { "job_id": "job-2025-32", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. Junior, but has some Cloud skills." },
  { "job_id": "job-2025-32", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Good for the AI/Data part of the sale." },
  { "job_id": "job-2025-33", "candidate_id": "cand-001", "match_type": "Good", "notes": "Strong match. Generalist Java/TS skills fit FDE profile perfectly." },
  { "job_id": "job-2025-33", "candidate_id": "cand-003", "match_type": "Good", "notes": "Strong match. Java/Data Integration background." },
  { "job_id": "job-2025-33", "candidate_id": "cand-005", "match_type": "Good", "notes": "Strong match. Full stack + Client facing ability." },
  { "job_id": "job-2025-33", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Deployment skills good, App building less so." },
  { "job_id": "job-2025-33", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Data/Analytics strong, Engineering weak." },
  { "job_id": "job-2025-34", "candidate_id": "cand-005", "match_type": "Good", "notes": "Strong match. React Native/Python is the exact stack." },
  { "job_id": "job-2025-34", "candidate_id": "cand-008", "match_type": "Medium", "notes": "Partial match. Mobile knowledge helps, but lacks Web/Backend." },
  { "job_id": "job-2025-34", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. React/Python skills present." },
  { "job_id": "job-2025-34", "candidate_id": "cand-006", "match_type": "Medium", "notes": "Partial match. React/Web skills fit." },
  { "job_id": "job-2025-34", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Python/AI knowledge." },
  { "job_id": "job-2025-35", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Strong Systems/Concurrency, but C++/Graphics gap." },
  { "job_id": "job-2025-35", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. iOS app level vs Engine level." },
  { "job_id": "job-2025-35", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-35", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Systems knowledge." },
  { "job_id": "job-2025-35", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-36", "candidate_id": "cand-007", "match_type": "Good", "notes": "Strong match. Exact skill set (Go/K8s/Terraform/Linux)." },
  { "job_id": "job-2025-36", "candidate_id": "cand-003", "match_type": "Good", "notes": "Strong match. Go/System Design fits well." },
  { "job_id": "job-2025-36", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. Junior, but teachable on tools." },
  { "job_id": "job-2025-36", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. AWS knowledge helps." },
  { "job_id": "job-2025-36", "candidate_id": "cand-002", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-37", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Strong networking/systems, but Rust/Wasm is specific." },
  { "job_id": "job-2025-37", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Go is close to Rust in domain, but syntax differs." },
  { "job_id": "job-2025-37", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-37", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-37", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-38", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. Frontend focus, but WebGL/C++ is a stretch." },
  { "job_id": "job-2025-38", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-38", "candidate_id": "cand-003", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-38", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-38", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-01", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch. Bootcamp grad." },
  { "job_id": "job-2025-03", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch. Data Science." },
  { "job_id": "job-2025-04", "candidate_id": "cand-006", "match_type": "Medium", "notes": "Partial match. Junior role potential if stack aligns." },
  { "job_id": "job-2025-04", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile." },
  { "job_id": "job-2025-06", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile." },
  { "job_id": "job-2025-06", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Knows ML, but not Infra." },
  { "job_id": "job-2025-07", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. C++ missing but strong engineering." },
  { "job_id": "job-2025-07", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Systems background." },
  { "job_id": "job-2025-08", "candidate_id": "cand-007", "match_type": "Poor", "notes": "Mismatch. Ops." },
  { "job_id": "job-2025-09", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch. Web." },
  { "job_id": "job-2025-09", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile." },
  { "job_id": "job-2025-10", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. ML background." },
  { "job_id": "job-2025-10", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-11", "candidate_id": "cand-002", "match_type": "Poor", "notes": "Mismatch. ML." },
  { "job_id": "job-2025-11", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile." },
  { "job_id": "job-2025-12", "candidate_id": "cand-007", "match_type": "Poor", "notes": "Mismatch. DevOps." },
  { "job_id": "job-2025-12", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch. Bootcamp." },
  { "job_id": "job-2025-12", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile." },
  { "job_id": "job-2025-13", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch. DS." },
  { "job_id": "job-2025-13", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch. Bootcamp." },
  { "job_id": "job-2025-14", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch. Web." },
  { "job_id": "job-2025-14", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile." },
  { "job_id": "job-2025-15", "candidate_id": "cand-001", "match_type": "Medium", "notes": "Partial match. Seniority gap." },
  { "job_id": "job-2025-15", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Detection models." },
  { "job_id": "job-2025-15", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch. Mobile." },
  { "job_id": "job-2025-16", "candidate_id": "cand-007", "match_type": "Poor", "notes": "Mismatch. Ops." },
  { "job_id": "job-2025-16", "candidate_id": "cand-002", "match_type": "Poor", "notes": "Mismatch. ML." },
  { "job_id": "job-2025-17", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Engineer." },
  { "job_id": "job-2025-17", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Infra." },
  { "job_id": "job-2025-17", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-18", "candidate_id": "cand-002", "match_type": "Poor", "notes": "Mismatch. ML." },
  { "job_id": "job-2025-18", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-18", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-19", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-19", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-19", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-20", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Git/Ops." },
  { "job_id": "job-2025-20", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-20", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-21", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch. Seniority." },
  { "job_id": "job-2025-21", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Algorithms." },
  { "job_id": "job-2025-21", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-22", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Math/Controls." },
  { "job_id": "job-2025-22", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Math/Physics." },
  { "job_id": "job-2025-22", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-23", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-23", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-23", "candidate_id": "cand-001", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-24", "candidate_id": "cand-005", "match_type": "Medium", "notes": "Partial match. SQL." },
  { "job_id": "job-2025-24", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-24", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-25", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-25", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-25", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-26", "candidate_id": "cand-002", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-26", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-26", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Backend strong." },
  { "job_id": "job-2025-27", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Math." },
  { "job_id": "job-2025-27", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-27", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-28", "candidate_id": "cand-002", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-28", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-29", "candidate_id": "cand-005", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-29", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-29", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-30", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-30", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-30", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-31", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-31", "candidate_id": "cand-007", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-31", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-32", "candidate_id": "cand-002", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-32", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-32", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-33", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Data skills." },
  { "job_id": "job-2025-33", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-33", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-34", "candidate_id": "cand-003", "match_type": "Medium", "notes": "Partial match. Backend strong." },
  { "job_id": "job-2025-34", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-34", "candidate_id": "cand-007", "match_type": "Medium", "notes": "Partial match. Backend/Ops." },
  { "job_id": "job-2025-35", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Math." },
  { "job_id": "job-2025-35", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Math." },
  { "job_id": "job-2025-35", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-36", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-36", "candidate_id": "cand-006", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-36", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-37", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. C++ history?" },
  { "job_id": "job-2025-37", "candidate_id": "cand-004", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-37", "candidate_id": "cand-008", "match_type": "Poor", "notes": "Mismatch." },
  { "job_id": "job-2025-38", "candidate_id": "cand-002", "match_type": "Medium", "notes": "Partial match. Math." },
  { "job_id": "job-2025-38", "candidate_id": "cand-004", "match_type": "Medium", "notes": "Partial match. Geometry." },
  { "job_id": "job-2025-38", "candidate_id": "cand-007", "match_type": "Poor", "notes": "Mismatch." }
]

# ==========================================
# 4. EXECUTION
# ==========================================
def write_files():
    # 1. Write New Job Files
    for job in new_jobs:
        filename = os.path.join(JOBS_DIR, f"{job['job_id']}.yaml")
        with open(filename, "w") as f:
            yaml.dump(job, f, sort_keys=False, default_flow_style=False)
        print(f"Created Job: {filename}")

    # 2. Write New Resume Files
    for cand in new_resumes:
        # NOTE: Using a specific naming convention to match your existing pattern
        # e.g., 'cand-007.json' based on candidate_id
        filename = os.path.join(RESUMES_DIR, f"{cand['candidate_id']}.json")
        with open(filename, "w") as f:
            json.dump(cand, f, indent=2)
        print(f"Created Resume: {filename}")

    # 3. Create Final Pairs List
    # We must ensure the 'job_path' and 'resume_path' fields exist,
    # as main.py likely expects them.
    final_pairs = []
    
    # Map for easy lookup to ensure file existence
    # (Assuming 1-30 are already there, and 31-38 we just created)
    # (Assuming cand-001 to 006 are there, and 007-008 we just created)
    
    for i, pair in enumerate(raw_pairs):
        pair_entry = {
            "id": f"pair-{i+1:03d}",
            "job_path": f"{JOBS_DIR}/{pair['job_id']}.yaml",
            "resume_path": f"{RESUMES_DIR}/{pair['candidate_id']}.json",
            "match_type": pair.get("match_type", "Unknown"), # Preserving metadata for analysis
            "notes": pair.get("notes", "")
        }
        final_pairs.append(pair_entry)

    # 4. Write the Master Pairs File
    with open(PAIRS_FILE, "w") as f:
        json.dump(final_pairs, f, indent=2)
    print(f"\n✅ Successfully overwrote {PAIRS_FILE} with {len(final_pairs)} pairs.")

if __name__ == "__main__":
    write_files()
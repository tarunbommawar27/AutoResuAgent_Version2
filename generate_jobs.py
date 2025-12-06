import os
import yaml

# Ensure the directory exists
output_dir = "data/jobs"
os.makedirs(output_dir, exist_ok=True)

# Full dataset of 30 jobs
jobs_data = [
    {{
        "job_id": "job-2025-01",
        "title": "Member of Technical Staff (Post-Training)",
        "company": "OpenAI",
        "location": "San Francisco, CA",
        "seniority": "Mid-Level",
        "required_skills": ["Python", "PyTorch", "Reinforcement Learning (RLHF/RLAIF)", "Distributed Training", "Algorithm Design"],
        "responsibilities": [
            "Design and implement novel post-training methods to improve model reasoning and instruction following.",
            "Scale reinforcement learning pipelines across thousands of GPUs to fine-tune next-generation frontier models.",
            "Develop automated evaluation harnesses to measure model alignment, safety, and factual accuracy.",
            "Collaborate with the pre-training team to analyze model checkpoints and optimize handover protocols.",
            "Debug complex distributed system issues in a high-velocity research environment."
        ],
        "nice_to_have_skills": ["Experience with PPO or DPO algorithms", "Kubernetes", "C++"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-15"}
    },
    {
        "job_id": "job-2025-02",
        "title": "Research Engineer, Alignment",
        "company": "Anthropic",
        "location": "San Francisco, CA",
        "seniority": "Senior",
        "required_skills": ["Python", "JAX", "Interpretability Research", "Large Language Models", "Mathematics"],
        "responsibilities": [
            "Investigate the internal representations of large language models to understand how they reason.",
            "Build tools and techniques to steer model behavior towards helpfulness and honesty (Constitutional AI).",
            "Design experiments to detect and mitigate reward hacking in reinforcement learning loops.",
            "Write production-quality code to run large-scale interpretability sweeps on Claude models.",
            "Publish technical reports and contribute to the broader AI safety community."
        ],
        "nice_to_have_skills": ["Rust", "Information Theory", "Visualization libraries (D3.js)"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-20"}
    },
    {
        "job_id": "job-2025-03",
        "title": "Senior Deep Learning Engineer (Inference)",
        "company": "NVIDIA",
        "location": "Santa Clara, CA",
        "seniority": "Senior",
        "required_skills": ["C++", "CUDA", "Python", "TensorRT", "LLM Optimization"],
        "responsibilities": [
            "Optimize inference kernels for trillion-parameter models on Blackwell architecture GPUs.",
            "Implement techniques like speculative decoding and KV-cache compression to reduce latency.",
            "Architect scalable serving solutions for high-throughput agentic workflows.",
            "Profile and analyze deep learning workloads to identify system bottlenecks.",
            "Collaborate with research partners to integrate novel attention mechanisms into production kernels."
        ],
        "nice_to_have_skills": ["Triton Inference Server", "MPI/NCCL", "Assembly optimization"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-10"}
    },
    {
        "job_id": "job-2025-04",
        "title": "Backend Engineer, Agentic Commerce",
        "company": "Stripe",
        "location": "Seattle, WA",
        "seniority": "Mid-Level",
        "required_skills": ["Java", "Go", "Distributed Systems", "API Design", "Temporal/Workflow Engines"],
        "responsibilities": [
            "Build the backend infrastructure supporting autonomous AI agents that perform financial transactions.",
            "Design idempotent payment APIs that handle high-concurrency requests from automated systems.",
            "Ensure 99.999% reliability for critical money movement services.",
            "Implement fraud detection hooks specifically designed for non-human transaction patterns.",
            "Scale database sharding strategies to accommodate growing agent-driven traffic."
        ],
        "nice_to_have_skills": ["Ruby", "Machine Learning familiarity", "AWS Lambda"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-05"}
    },
    {
        "job_id": "job-2025-05",
        "title": "Research Scientist, Reasoning",
        "company": "Google DeepMind",
        "location": "London, UK",
        "seniority": "Staff",
        "required_skills": ["Python", "TensorFlow/JAX", "Chain-of-Thought Reasoning", "Mathematics", "Academic Writing"],
        "responsibilities": [
            "Lead research into improving multi-step reasoning and planning capabilities of Gemini models.",
            "Develop novel training objectives that encourage self-correction and reflection.",
            "Propose and validate hypotheses regarding the limits of current transformer architectures.",
            "Mentor junior researchers and engineers.",
            "Collaborate with the Gemini product team to transfer research breakthroughs into production."
        ],
        "nice_to_have_skills": ["Formal Logic", "Theorem Proving", "Robotics experience"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-10-28"}
    },
    {
        "job_id": "job-2025-06",
        "title": "Senior ML Systems Engineer",
        "company": "Databricks",
        "location": "San Francisco, CA",
        "seniority": "Senior",
        "required_skills": ["Kubernetes", "Go", "Python", "GPU Infrastructure", "Spark/Ray"],
        "responsibilities": [
            "Architect and build the compute substrate for training MosaicML foundation models.",
            "Optimize job scheduling algorithms for massive multi-node GPU clusters.",
            "Develop efficient model checkpointing and recovery systems to minimize training downtime.",
            "Build observability tools to monitor hardware health and training metrics at scale.",
            "Contribute to open-source projects like MLflow and Ray."
        ],
        "nice_to_have_skills": ["Slurm", "InfiniBand networking", "Rust"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-22"}
    },
    {
        "job_id": "job-2025-07",
        "title": "Software Engineer, Perception",
        "company": "Waymo",
        "location": "Mountain View, CA",
        "seniority": "Mid-Level",
        "required_skills": ["C++", "Python", "Computer Vision", "LiDAR Processing", "Linear Algebra"],
        "responsibilities": [
            "Develop real-time perception algorithms for detecting pedestrians and cyclists in complex urban environments.",
            "Integrate Vision-Language Models (VLMs) to improve semantic understanding of road scenes.",
            "Optimize code for latency-critical onboard embedded systems.",
            "Validate algorithm performance using large-scale simulation and log replay tools.",
            "Work closely with the planning team to ensure perception outputs meet safety requirements."
        ],
        "nice_to_have_skills": ["CUDA", "TensorRT", "Sensor Fusion"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-01"}
    },
    {
        "job_id": "job-2025-08",
        "title": "Full Stack Engineer, AI Product",
        "company": "Notion",
        "location": "New York, NY",
        "seniority": "Mid-Level",
        "required_skills": ["TypeScript", "React", "Node.js", "Postgres", "OpenAI API / LLM Integration"],
        "responsibilities": [
            "Build intuitive user interfaces for Notion's AI writing and organization features.",
            "Develop backend services that orchestrate calls to multiple LLM providers (Anthropic, OpenAI).",
            "Optimize frontend performance for real-time streaming of generated text.",
            "Implement RAG (Retrieval Augmented Generation) pipelines to ground AI answers in user data.",
            "Collaborate with designers to create novel human-AI interaction patterns."
        ],
        "nice_to_have_skills": ["Next.js", "Vector Databases (Pinecone/Weaviate)", "WebAssembly"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-18"}
    },
    {
        "job_id": "job-2025-09",
        "title": "Machine Learning Engineer, Llama",
        "company": "Meta",
        "location": "Menlo Park, CA",
        "seniority": "Mid-Level",
        "required_skills": ["Python", "PyTorch", "Distributed Training", "Model Quantization", "Data Engineering"],
        "responsibilities": [
            "Curate and process massive datasets for training future versions of Llama.",
            "Implement efficient data loading pipelines to saturate H100 GPU clusters.",
            "Experiment with new architectural components to improve model efficiency.",
            "Run ablation studies to determine the impact of different data mixtures.",
            "Collaborate with the open-source team to prepare model weights for public release."
        ],
        "nice_to_have_skills": ["C++", "CUDA", "Hadoop/Hive"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-12"}
    },
    {
        "job_id": "job-2025-10",
        "title": "Mission Software Engineer",
        "company": "Anduril",
        "location": "Costa Mesa, CA",
        "seniority": "Senior",
        "required_skills": ["C++", "Rust", "Distributed Systems", "Network Programming", "Real-time Systems"],
        "responsibilities": [
            "Build the Lattice operating system that coordinates autonomous assets in the field.",
            "Develop mesh networking protocols for intermittent and low-bandwidth environments.",
            "Implement consensus algorithms for multi-agent coordination without central control.",
            "Optimize software for deployment on edge compute hardware (NVIDIA Jetson).",
            "Lead field testing exercises to validate software reliability in real-world conditions."
        ],
        "nice_to_have_skills": ["Geospatial data processing", "Robotics Operating System (ROS)", "Security Clearance"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-10-15"}
    },
    {
        "job_id": "job-2025-11",
        "title": "Software Development Engineer II",
        "company": "Amazon",
        "location": "Seattle, WA",
        "seniority": "Mid-Level",
        "required_skills": ["Java", "AWS (DynamoDB, ECS, S3)", "System Design", "Operational Excellence", "Microservices"],
        "responsibilities": [
            "Design and build the control plane for AWS Bedrock, managing millions of concurrent model invocations.",
            "Implement rate limiting and metering systems for Generative AI APIs.",
            "Ensure high availability and fault tolerance across multiple AWS regions.",
            "Participate in on-call rotations and drive root cause analysis for production incidents.",
            "Optimize service latency to meet strict SLAs for enterprise customers."
        ],
        "nice_to_have_skills": ["Python", "Rust", "Knowledge of LLM serving"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-25"}
    },
    {
        "job_id": "job-2025-12",
        "title": "Senior Data Scientist, Product",
        "company": "Netflix",
        "location": "Los Gatos, CA",
        "seniority": "Senior",
        "required_skills": ["Python", "SQL", "Causal Inference", "A/B Testing", "Machine Learning"],
        "responsibilities": [
            "Lead experimentation strategy for AI-generated content personalized thumbnails.",
            "Develop causal models to understand the long-term retention impact of interactive storytelling.",
            "Partner with engineering to instrument new logging for complex user sessions.",
            "Communicate insights to product leadership to influence the content roadmap.",
            "Build automated dashboards to monitor the health of recommendation algorithms."
        ],
        "nice_to_have_skills": ["Spark", "Tableau", "Econometrics"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-08"}
    },
    {
        "job_id": "job-2025-13",
        "title": "Member of Technical Staff, Infrastructure",
        "company": "xAI",
        "location": "Palo Alto, CA",
        "seniority": "Senior",
        "required_skills": ["Rust", "Python", "Kubernetes", "HPC (High Performance Computing)", "RDMA"],
        "responsibilities": [
            "Build the world's largest GPU training cluster, optimizing network topology and storage I/O.",
            "Develop high-performance data loaders in Rust to feed models at line rate.",
            "Create custom schedulers to maximize GPU utilization across thousands of nodes.",
            "Debug hardware failures at scale and implement automated remediation systems.",
            "Work directly with researchers to support massive training runs."
        ],
        "nice_to_have_skills": ["Kernel development", "Hardware design knowledge", "Electrical Engineering background"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-28"}
    },
    {
        "job_id": "job-2025-14",
        "title": "Core Model Engineer",
        "company": "Mistral AI",
        "location": "Paris, France",
        "seniority": "Mid-Level",
        "required_skills": ["Python", "PyTorch", "FlashAttention", "Model Optimization", "English & French (Professional)"],
        "responsibilities": [
            "Implement state-of-the-art transformer architectures for open-weight models.",
            "Optimize training loops to improve convergence speed and compute efficiency.",
            "Develop Mixture-of-Experts (MoE) routing algorithms.",
            "Collaborate on the creation of high-quality synthetic training datasets.",
            "Deploy models to internal inference clusters for benchmarking."
        ],
        "nice_to_have_skills": ["C++", "Megatron-LM", "Rust"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-14"}
    },
    {
        "job_id": "job-2025-15",
        "title": "Senior Software Engineer, Safety",
        "company": "Discord",
        "location": "San Francisco, CA",
        "seniority": "Senior",
        "required_skills": ["Python", "Go", "Real-time Stream Processing", "Machine Learning Systems", "Cassandra/ScyllaDB"],
        "responsibilities": [
            "Build real-time content moderation systems processing billions of messages per day.",
            "Integrate on-device and cloud-based ML models to detect harmful content.",
            "Architect scalable privacy-preserving systems for user data.",
            "Lead technical initiatives to combat platform abuse and spam.",
            "Mentor junior engineers in distributed systems best practices."
        ],
        "nice_to_have_skills": ["Rust", "Elixir", "Graph Neural Networks"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-10-30"}
    },
    {
        "job_id": "job-2025-16",
        "title": "Senior Frontend Engineer",
        "company": "Linear",
        "location": "Remote",
        "seniority": "Senior",
        "required_skills": ["TypeScript", "React", "Electron", "CSS/Styled Components", "Local-first Architecture"],
        "responsibilities": [
            "Build high-performance, native-feeling user interfaces for Linear's issue tracking app.",
            "Implement offline-first capabilities using local databases (Sync engine).",
            "Design and build AI-assisted features that feel magical but unobtrusive.",
            "Optimize rendering performance to maintain 60fps on all interactions.",
            "Contribute to the design system and maintain high visual standards."
        ],
        "nice_to_have_skills": ["WebGL", "Prosemirror", "GraphQL"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-02"}
    },
    {
        "job_id": "job-2025-17",
        "title": "Machine Learning Engineer",
        "company": "Scale AI",
        "location": "San Francisco, CA",
        "seniority": "Junior",
        "required_skills": ["Python", "PyTorch", "Generative AI", "Data Pipelines", "API Integration"],
        "responsibilities": [
            "Develop automated pipelines for generating high-quality synthetic training data.",
            "Fine-tune open-source models (Llama, Mistral) for specific domain tasks.",
            "Build evaluation metrics to assess the quality of AI-generated content.",
            "Collaborate with operations teams to manage human-in-the-loop workflows.",
            "Write scripts to clean and format massive datasets for enterprise clients."
        ],
        "nice_to_have_skills": ["Docker", "FastAPI", "Prompt Engineering"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-19"}
    },
    {
        "job_id": "job-2025-18",
        "title": "Staff Backend Engineer",
        "company": "Uber",
        "location": "San Francisco, CA",
        "seniority": "Staff",
        "required_skills": ["Go", "Java", "Microservices", "High Availability", "Kafka"],
        "responsibilities": [
            "Architect the next generation of Uber's marketplace matching engine.",
            "Design systems that handle millions of real-time events per second.",
            "Lead cross-functional engineering efforts to improve platform reliability.",
            "Define technical standards and best practices for the backend engineering organization.",
            "Resolve high-severity production incidents and implement long-term fixes."
        ],
        "nice_to_have_skills": ["Redis", "Optimization Algorithms", "Google Cloud Platform"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-10-25"}
    },
    {
        "job_id": "job-2025-19",
        "title": "Computational Biologist / ML Researcher",
        "company": "Isomorphic Labs",
        "location": "London, UK",
        "seniority": "Senior",
        "required_skills": ["Python", "JAX/PyTorch", "Structural Biology", "Geometric Deep Learning", "Protein Folding"],
        "responsibilities": [
            "Apply deep learning methods to predict protein-ligand interactions.",
            "Develop generative models for de novo drug design.",
            "Collaborate with chemists and biologists to validate model predictions.",
            "Analyze large-scale genomic and proteomic datasets.",
            "Publish research in top scientific journals."
        ],
        "nice_to_have_skills": ["Molecular Dynamics", "Cheminformatics", "PhD in relevant field"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-16"}
    },
    {
        "job_id": "job-2025-20",
        "title": "Open Source ML Engineer",
        "company": "Hugging Face",
        "location": "Remote",
        "seniority": "Mid-Level",
        "required_skills": ["Python", "PyTorch", "Transformers Library", "Open Source Contribution", "Git"],
        "responsibilities": [
            "Maintain and improve the Hugging Face Transformers and Accelerate libraries.",
            "Implement new model architectures from recent research papers.",
            "Optimize training scripts for ease of use and performance.",
            "Engage with the community on GitHub and Discord to resolve issues.",
            "Create tutorials and documentation to help users leverage open-source AI."
        ],
        "nice_to_have_skills": ["JAX/Flax", "ONNX", "TensorFlow"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-26"}
    },
    {
        "job_id": "job-2025-21",
        "title": "Senior Systems Engineer",
        "company": "Pinecone",
        "location": "New York, NY",
        "seniority": "Senior",
        "required_skills": ["Go", "Rust", "Kubernetes", "Distributed Databases", "Vector Search Algorithms"],
        "responsibilities": [
            "Build and scale the storage engine for a high-performance vector database.",
            "Optimize HNSW and other indexing algorithms for latency and recall.",
            "Design systems for multi-tenant data isolation and security.",
            "Implement replication and sharding strategies for global availability.",
            "Mentor engineers and drive technical decision-making."
        ],
        "nice_to_have_skills": ["C++", "Prometheus/Grafana", "AWS EKS"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-12"}
    },
    {
        "job_id": "job-2025-22",
        "title": "Flight Software Engineer",
        "company": "SpaceX",
        "location": "Hawthorne, CA",
        "seniority": "Mid-Level",
        "required_skills": ["C++", "Python", "Embedded Systems", "Real-time OS (RTOS)", "Control Systems"],
        "responsibilities": [
            "Develop safety-critical flight software for Starship vehicles.",
            "Implement guidance, navigation, and control (GNC) algorithms.",
            "Write efficient driver code for sensors and actuators.",
            "Participate in hardware-in-the-loop (HITL) testing and launch support.",
            "Analyze flight telemetry to improve system performance."
        ],
        "nice_to_have_skills": ["Rust", "FPGA programming", "Physics simulation"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-05"}
    },
    {
        "job_id": "job-2025-23",
        "title": "Humanoid Control Engineer",
        "company": "Figure",
        "location": "Sunnyvale, CA",
        "seniority": "Senior",
        "required_skills": ["C++", "Python", "Model Predictive Control (MPC)", "Reinforcement Learning", "Robotics"],
        "responsibilities": [
            "Develop whole-body control algorithms for humanoid robots.",
            "Implement locomotion and manipulation planners.",
            "Bridge the gap between simulation (Sim-to-Real) and physical hardware.",
            "Optimize control loops for real-time performance on embedded computers.",
            "Collaborate with mechanical engineers to design actuation systems."
        ],
        "nice_to_have_skills": ["MuJoCo/Isaac Gym", "ROS2", "EtherCAT"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-21"}
    },
    {
        "job_id": "job-2025-24",
        "title": "Data Engineer, AI",
        "company": "Snowflake",
        "location": "San Mateo, CA",
        "seniority": "Mid-Level",
        "required_skills": ["SQL", "Python", "Snowflake", "Airflow", "Data Modeling"],
        "responsibilities": [
            "Build scalable data pipelines to prepare unstructured data for AI models (Cortex).",
            "Optimize SQL queries and data structures for cost and performance.",
            "Implement data governance and security controls for sensitive enterprise data.",
            "Collaborate with product teams to integrate AI features into the Data Cloud.",
            "Monitor pipeline health and data quality."
        ],
        "nice_to_have_skills": ["Java", "dbt", "Vector Search"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-09"}
    },
    {
        "job_id": "job-2025-25",
        "title": "Senior Backend Engineer",
        "company": "Cohere",
        "location": "Toronto, Canada",
        "seniority": "Senior",
        "required_skills": ["Go", "Python", "gRPC", "Kubernetes", "Cloud Infrastructure (GCP/AWS)"],
        "responsibilities": [
            "Design and build the high-performance API serving Cohere's Enterprise LLMs.",
            "Implement fine-grained rate limiting and usage tracking for billing.",
            "Optimize inter-service communication latency.",
            "Ensure data privacy and compliance for enterprise customers.",
            "Scale the platform to handle exponential traffic growth."
        ],
        "nice_to_have_skills": ["Terraform", "Service Mesh", "PostgreSQL"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-15"}
    },
    {
        "job_id": "job-2025-26",
        "title": "Full Stack Engineer",
        "company": "Airbnb",
        "location": "San Francisco, CA",
        "seniority": "Mid-Level",
        "required_skills": ["Java", "JavaScript/TypeScript", "React", "GraphQL", "SQL"],
        "responsibilities": [
            "Develop features for the guest travel planning experience.",
            "Integrate AI-powered recommendations into the search flow.",
            "Build responsive and accessible user interfaces.",
            "Write efficient backend code to serve data to the frontend.",
            "Participate in code reviews and design discussions."
        ],
        "nice_to_have_skills": ["Kotlin", "Swift/Android", "Design Systems"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-03"}
    },
    {
        "job_id": "job-2025-27",
        "title": "AI Infrastructure Engineer",
        "company": "Tesla",
        "location": "Palo Alto, CA",
        "seniority": "Senior",
        "required_skills": ["Python", "C++", "PyTorch", "Distributed Systems", "Linux Kernel"],
        "responsibilities": [
            "Optimize the software stack for the Dojo supercomputer.",
            "Improve the efficiency of large-scale distributed training jobs.",
            "Debug low-level networking and storage issues in the training cluster.",
            "Develop tools for automated model evaluation and deployment.",
            "Work with hardware engineers to co-design future compute platforms."
        ],
        "nice_to_have_skills": ["Compiler optimization", "CUDA", "Kubernetes"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-17"}
    },
    {
        "job_id": "job-2025-28",
        "title": "Ruby/Rails Engineer (Intelligence)",
        "company": "Shopify",
        "location": "Remote",
        "seniority": "Senior",
        "required_skills": ["Ruby on Rails", "Python", "GraphQL", "MySQL", "AI Application Integration"],
        "responsibilities": [
            "Build backend services for 'Shopify Magic' AI features.",
            "Design scalable architectures to process merchant data safely.",
            "Integrate third-party LLM APIs with Shopify's core commerce platform.",
            "Optimize background jobs and data processing pipelines.",
            "Mentor junior developers and review code."
        ],
        "nice_to_have_skills": ["Go", "React", "Vector Stores"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-07"}
    },
    {
        "job_id": "job-2025-29",
        "title": "Senior ML Engineer, Trust & Safety",
        "company": "Pinterest",
        "location": "San Francisco, CA",
        "seniority": "Senior",
        "required_skills": ["Python", "PyTorch", "Computer Vision", "NLP", "Big Data (Spark/Flink)"],
        "responsibilities": [
            "Develop multi-modal models to detect unsafe images and text.",
            "Build real-time classification systems to filter content at upload.",
            "Analyze adversarial patterns and update models accordingly.",
            "Collaborate with policy teams to define safety guidelines.",
            "Scale training pipelines to handle petabytes of data."
        ],
        "nice_to_have_skills": ["Scala", "AWS", "Graph Mining"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-13"}
    },
    {
        "job_id": "job-2025-30",
        "title": "Software Engineer, Core",
        "company": "Poolside",
        "location": "San Francisco, CA",
        "seniority": "Mid-Level",
        "required_skills": ["Python", "Rust", "Code Generation LLMs", "VS Code Extensions", "Distributed Systems"],
        "responsibilities": [
            "Build the infrastructure for training models specialized in code generation.",
            "Develop IDE extensions that integrate seamlessly with developer workflows.",
            "Design evaluation benchmarks for coding tasks.",
            "Optimize inference latency for real-time code completion.",
            "Collaborate with a small, high-velocity team."
        ],
        "nice_to_have_skills": ["TypeScript", "LSP (Language Server Protocol)", "C++"],
        "extra_metadata": {"employment_type": "Full-time", "posted_on": "2025-11-29"}
    }}
]

# Iterate and write to YAML files
for job in jobs_data:
    filename = os.path.join(output_dir, f"{job['job_id']}.yaml")
    
    # Writing the file
    with open(filename, "w") as f:
        # sort_keys=False ensures the order matches the dictionary order
        # default_flow_style=False ensures list items are on new lines (block style)
        yaml.dump(job, f, sort_keys=False, default_flow_style=False)
        
    print(f"Created: {filename}")

print("\nSuccess! Created all 30 job files in data/jobs/")
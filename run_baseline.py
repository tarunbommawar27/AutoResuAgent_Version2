from src.agent import AgentExecutor
from src.embeddings import SentenceBertEncoder
from src.llm.openai_client import OpenAILLMClient
from pathlib import Path
import asyncio
import os
import shutil
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

async def main():
    # 2. Get API Key
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found.")
        print("Please ensure your .env file is set up correctly.")
        return

    print(f"🔑 API Key detected: {api_key[:5]}...{api_key[-4:]}")

    try:
        # 3. Initialize components
        llm = OpenAILLMClient(api_key=api_key)
        encoder = SentenceBertEncoder()
        executor = AgentExecutor(llm, encoder)

        print("🚀 Starting Baseline Generation...")
        
        # 4. Run the Job/Resume pair
        # This will generate outputs/OpenAI_.../resume.tex (default name)
        await executor.run_single_job(
            Path("data/jobs/job-2025-01.yaml"),
            Path("data/resumes/cand-007.json"),
            mode="baseline"
        )

        # 5. RENAME the output file to _baseline
        # We assume the output folder structure based on the job details
        # (Company: OpenAI, Title: Member of Technical Staff (Post-Training))
        output_dir = Path("outputs/OpenAI_Member_of_Technical_Staff_(Post-Training)")
        
        original_tex = output_dir / "resume.tex"
        new_tex_name = output_dir / "resume_baseline.tex"

        if original_tex.exists():
            # Rename the file
            if new_tex_name.exists():
                os.remove(new_tex_name) # Remove old baseline if it exists
            
            os.rename(original_tex, new_tex_name)
            
            print("✅ Success!")
            print(f"📄 Baseline TEX file saved at: {new_tex_name}")
        else:
            print(f"⚠️  Warning: Could not find generated file at {original_tex}")
    
    except Exception as e:
        print(f"❌ Error during execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())
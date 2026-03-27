# Simple test to verify the batch file creation functions
import sys
sys.path.append('.')

from deploy_env import create_run_script, update_generate_bat

print("Testing batch file creation...")
create_run_script()  # This will also call update_generate_bat()
print("Batch file creation test completed.")
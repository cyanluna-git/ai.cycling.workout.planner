#!/usr/bin/env python3
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

def flat_to_nested(flat_step: Dict[str, Any]) -> Dict[str, Any]:
    step_type = flat_step.get("type", "steady")
    
    if step_type == "warmup":
        return {
            "duration": flat_step.get("duration_sec", 0),
            "power": {
                "start": flat_step.get("start_power", 50),
                "end": flat_step.get("end_power", 75),
                "units": "%ftp"
            },
            "ramp": True,
            "warmup": True
        }
    
    elif step_type == "cooldown":
        return {
            "duration": flat_step.get("duration_sec", 0),
            "power": {
                "start": flat_step.get("start_power", 70),
                "end": flat_step.get("end_power", 40),
                "units": "%ftp"
            },
            "ramp": True,
            "cooldown": True
        }
    
    elif step_type == "intervals" and "repeat" in flat_step:
        on_step = {
            "duration": flat_step.get("on_sec", 0),
            "power": {
                "value": flat_step.get("on_power", 100),
                "units": "%ftp"
            }
        }
        off_step = {
            "duration": flat_step.get("off_sec", 0),
            "power": {
                "value": flat_step.get("off_power", 50),
                "units": "%ftp"
            }
        }
        return {
            "duration": 0,
            "repeat": flat_step["repeat"],
            "steps": [on_step, off_step]
        }
    
    elif step_type == "ramp":
        return {
            "duration": flat_step.get("duration_sec", 0),
            "power": {
                "start": flat_step.get("start_power", 50),
                "end": flat_step.get("end_power", 100),
                "units": "%ftp"
            },
            "ramp": True
        }
    
    else:
        nested = {"duration": flat_step.get("duration_sec", 0)}
        
        if "start_power" in flat_step and "end_power" in flat_step:
            nested["power"] = {
                "start": flat_step["start_power"],
                "end": flat_step["end_power"],
                "units": "%ftp"
            }
            nested["ramp"] = True
        elif "power" in flat_step:
            nested["power"] = {
                "value": flat_step["power"],
                "units": "%ftp"
            }
        
        return nested

def migrate_profile(steps_json_str: str) -> str:
    flat_data = json.loads(steps_json_str)
    flat_steps = flat_data.get("steps", [])
    nested_steps = [flat_to_nested(step) for step in flat_steps]
    return json.dumps({"steps": nested_steps})

def main():
    db_path = Path("data/workout_profiles.db")
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return 1
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"workout_profiles.db.backup_{timestamp}"
    print(f"Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, name, steps_json FROM workout_profiles")
        profiles = cursor.fetchall()
        
        print(f"Migrating {len(profiles)} profiles...")
        
        migrated_count = 0
        
        for profile_id, name, steps_json_str in profiles:
            try:
                nested_json = migrate_profile(steps_json_str)
                cursor.execute(
                    "UPDATE workout_profiles SET steps_json = ? WHERE id = ?",
                    (nested_json, profile_id)
                )
                migrated_count += 1
                if migrated_count % 10 == 0:
                    print(f"  Migrated {migrated_count}/{len(profiles)}...")
            except Exception as e:
                print(f"Failed to migrate profile {profile_id} ({name}): {e}")
        
        conn.commit()
        
        print(f"\nMigration complete!")
        print(f"  Migrated: {migrated_count}")
        print(f"  Backup: {backup_path}")
        
        cursor.execute("SELECT id, name, steps_json FROM workout_profiles LIMIT 1")
        row = cursor.fetchone()
        if row:
            steps = json.loads(row[2])
            print(f"\nSample (after migration):")
            print(f"  Profile: {row[1]}")
            print(f"  Format: {json.dumps(steps, indent=2)[:300]}...")
        
        return 0
    
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        return 1
    
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    sys.exit(main())

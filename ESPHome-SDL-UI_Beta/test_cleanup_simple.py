#!/usr/bin/env python3

# Simple test to check action cleanup logic
test_sensor = {
    'id': 'vibration_sensor',
    'on_press': {
        'then': [
            {'rtttl.play': 'ding:d=4,o=5,b=250:p,e,c'}
        ]
    }
}

action_name = 'rtttl.play'
trigger = 'on_press'

print("Before:")
print(f"  Sensor has on_press: {trigger in test_sensor}")
print(f"  on_press config: {test_sensor[trigger]}")

if trigger in test_sensor:
    trigger_config = test_sensor[trigger]
    print(f"  trigger_config is dict: {isinstance(trigger_config, dict)}")
    print(f"  has 'then': {'then' in trigger_config}")

    if isinstance(trigger_config, dict) and 'then' in trigger_config:
        original_actions = trigger_config['then'] if isinstance(trigger_config['then'], list) else [trigger_config['then']]
        print(f"  original_actions: {original_actions}")

        filtered_actions = []
        removed_count = 0

        for action in original_actions:
            print(f"    Checking action: {action}")
            print(f"      is dict: {isinstance(action, dict)}")
            print(f"      has '{action_name}': {action_name in action if isinstance(action, dict) else False}")

            if isinstance(action, dict) and action_name in action:
                print(f"      -> REMOVING")
                removed_count += 1
            else:
                print(f"      -> KEEPING")
                filtered_actions.append(action)

        print(f"\nRemoved count: {removed_count}")
        print(f"Filtered actions: {filtered_actions}")

        if len(filtered_actions) == 0:
            print(f"Deleting {trigger} from sensor")
            del test_sensor[trigger]
        else:
            trigger_config['then'] = filtered_actions

print("\nAfter:")
print(f"  Sensor: {test_sensor}")

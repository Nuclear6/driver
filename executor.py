import time
from typing import List

import pyautogui
from brain import (
    extract_high_level_plan_and_actions,
    extract_structured_actions,
    plan_next_step_actions,
)
from ocr_draw import annotate_image_with_ocr
from typings import Action, LabelMap, Context
from utils import image_to_base64


def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save("screenshot.png")
    return "./screenshot.png"


def start(task: str):
    screenshot = take_screenshot()
    label_map, output_image_path = annotate_image_with_ocr(screenshot)

    context: Context = {
        "task": task,
        "history": [],
        "high_level_plan": "",
        "actions_history": [],
    }
    plan_and_actions = plan_next_step_actions(
        context=context,
        image=image_to_base64(output_image_path),
    )
    if plan_and_actions:
        high_level_plan, str_actions = extract_high_level_plan_and_actions(
            plan_and_actions
        )
        context["high_level_plan"] = high_level_plan or ""
    else:
        raise Exception(f"No plan and actions were written: {plan_and_actions}")

    parse_actions_and_execute(
        label_map=label_map, context=context, str_actions=str_actions
    )


def next_step(context: Context):
    screenshot = take_screenshot()
    label_map, output_image_path = annotate_image_with_ocr(screenshot)
    str_actions = plan_next_step_actions(
        context=context,
        image=image_to_base64(output_image_path),
    )
    parse_actions_and_execute(
        label_map=label_map, context=context, str_actions=str_actions
    )


def parse_actions_and_execute(
    context: Context, label_map: LabelMap, str_actions: str | None
):
    if str_actions:
        actions = extract_structured_actions(input=str_actions) or []
        context["actions_history"].append(actions)
    else:
        raise Exception(f"No actions found on the plan: {str_actions}")

    if len(actions) > 0:
        execute(context, label_map=label_map, actions=actions)
    else:
        raise Exception(f"No actions extracted: {actions}")


def execute(context: Context, label_map: LabelMap, actions: List[Action]):
    print("\n\n> Executing actions\n")

    for action in actions:
        if action["action"] == "CLICK":
            if not action["parameter"] in label_map:
                print(
                    f"WARN: Label {action['parameter']} not present in the screenshot, skipping CLICK action"
                )
                continue
            item = label_map[action["parameter"]]
            print(f"Clicking {item}")
            pyautogui.moveTo(
                round(item["position"][0] + 12) / 2,
                round(item["position"][1] + 12) / 2,
                duration=1,
            )
            time.sleep(1)
            pyautogui.click()
        elif action["action"] == "TYPE":
            print(f"Typing {action['parameter']}")
            pyautogui.write(action["parameter"], interval=0.25)
        elif action["action"] == "REFRESH":
            print("Refreshing screenshot")
            next_step(context)
        else:
            print("Unknown action")
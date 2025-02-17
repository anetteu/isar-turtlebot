import logging
import time
from logging import Logger
from typing import Any, Optional, Sequence, Tuple

from robot_interface.models.geometry.frame import Frame
from robot_interface.models.geometry.joints import Joints
from robot_interface.models.geometry.orientation import Orientation
from robot_interface.models.geometry.pose import Pose
from robot_interface.models.geometry.position import Position
from robot_interface.models.inspection.inspection import (
    Inspection,
    InspectionResult,
)
from robot_interface.models.mission import DriveToPose, MissionStatus, Step
from robot_interface.robot_interface import RobotInterface

from isar_turtlebot.models.turtlebot_status import TurtlebotStatus
from isar_turtlebot.ros_bridge.ros_bridge import RosBridge


class Robot(RobotInterface):
    def __init__(self):
        self.logger: Logger = logging.getLogger("robot")

        self.bridge: RosBridge = RosBridge()

    def schedule_step(self, step: Step) -> Tuple[bool, Optional[Any], Optional[Joints]]:

        if isinstance(step, DriveToPose):
            previous_run_id: str = self.get_run_id()
            pose_message: dict = {
                "goal": {
                    "target_pose": {
                        "header": {
                            "seq": 0,
                            "stamp": {"secs": 1533, "nsecs": 746000000},
                            "frame_id": "map",
                        },
                        "pose": {
                            "position": {
                                "x": step.pose.position.x,
                                "y": step.pose.position.y,
                                "z": step.pose.position.z,
                            },
                            "orientation": {
                                "x": step.pose.orientation.x,
                                "y": step.pose.orientation.y,
                                "z": step.pose.orientation.z,
                                "w": step.pose.orientation.w,
                            },
                        },
                    }
                },
            }

            self.bridge.execute_task.publish(message=pose_message)
            run_id: str = self.wait_for_updated_task(previous_run_id=previous_run_id)
            return True, run_id, None

    def get_run_id(self) -> str:
        status_msg: dict = self.bridge.mission_status.get_value()
        try:
            run_id: str = status_msg["status_list"][0]["goal_id"]["id"]
            return run_id
        except KeyError as e:
            self.logger.error(e)
            raise

    def wait_for_updated_task(self, previous_run_id: str, timeout: int = 20) -> str:
        start_time: float = time.time()
        current_run_id: str = self.get_run_id()

        while current_run_id == previous_run_id:
            time.sleep(0.1)
            execution_time: float = time.time() - start_time
            if execution_time > timeout:
                raise TimeoutError(
                    f"Scheduling of task for TurtleBot3 timed out. Run ID: {current_run_id}"
                )
            current_run_id = self.get_run_id()

        return current_run_id

    def mission_scheduled(self) -> bool:
        return False

    def mission_status(self, mission_id: Any) -> MissionStatus:
        message: dict = self.bridge.mission_status.get_value()
        turtle_status: TurtlebotStatus = TurtlebotStatus.map_to_turtlebot_status(
            message["status_list"][0]["status"]
        )
        mission_status: MissionStatus = TurtlebotStatus.get_mission_status(
            status=turtle_status
        )
        return mission_status

    def abort_mission(self) -> bool:
        return True

    def log_status(
        self, mission_id: Any, mission_status: MissionStatus, current_step: Step
    ):
        self.logger.info(f"Mission ID: {mission_id}")
        self.logger.info(f"Mission Status: {mission_status}")
        self.logger.info(f"Current Step: {current_step}")

    def get_inspection_references(
        self, vendor_mission_id: Any, current_step: Step
    ) -> Sequence[Inspection]:
        return []

    def download_inspection_result(
        self, inspection: Inspection
    ) -> Optional[InspectionResult]:
        return None

    def robot_pose(self) -> Pose:
        pose: Pose = Pose(
            position=Position(x=1, y=1, z=1, frame=Frame.Robot),
            orientation=Orientation(x=0, y=0, z=0, w=1, frame=Frame.Robot),
            frame=Frame.Robot,
        )
        return pose

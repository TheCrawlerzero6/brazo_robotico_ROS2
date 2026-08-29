# Brazo robótico ROS 2

Paquete ROS 2 Jazzy para simular en Gazebo Sim un brazo robótico fijo de tres grados de libertad.

## Componentes

- Modelo URDF/Xacro con cuatro eslabones físicos (`link1` a `link4`).
- Mundo SDF con suelo, iluminación, gravedad y física.
- `gz_ros2_control` con un `JointTrajectoryController` para `joint1`, `joint2` y `joint3`.
- Secuencia automática de diez poses mediante `FollowJointTrajectory`.
- Lanzamiento opcional de RViz para inspección manual del modelo.

## Dependencias

Ubuntu 24.04, ROS 2 Jazzy y Gazebo Sim. Instala las dependencias de ROS indicadas en `package.xml`, o ejecuta:

```bash
sudo apt update
sudo apt install -y \
  ros-jazzy-xacro \
  ros-jazzy-ros-gz \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-tf2-tools
```

## Compilar y ejecutar

Desde la raíz del workspace:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select bajana_description
source install/setup.bash
ros2 launch bajana_description gazebo.launch.py
```

Para visualizar y mover el modelo manualmente en RViz:

```bash
ros2 launch bajana_description display.launch.py
```
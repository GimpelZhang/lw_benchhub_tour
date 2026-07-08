#!/usr/bin/env python3
"""Generate double_piper_description.urdf by duplicating the single-arm piper URDF
with _l/_r suffixes + a torso root. Resolves the T3 #1 risk (no verified double-piper URDF)
deterministically, reusing the proven single-arm kinematics. Joint names match the sim
(joint1_l..joint6_l, joint1_r..joint6_r) per double_piper.py's action term."""
import xml.etree.ElementTree as ET
from pathlib import Path

SRC = Path("/mnt/robot/lw_benchhub/lw_benchhub/utils/piper_description/urdf/piper_description.urdf")
OUT = Path("/mnt/robot/stage4_flywheel/curobo/double_piper_description.urdf")
LATERAL = 0.15  # ±0.15 m Y, matches reach_gate ARM_LATERAL_OFFSET

tree = ET.parse(SRC)
src_root = tree.getroot()

new_robot = ET.Element("robot", {"name": "double_piper"})

# Torso root link (minimal; cuRobo's chain starts at base_link_{l,r} so this is just a root).
torso = ET.SubElement(new_robot, "link", {"name": "base"})
ET.SubElement(torso, "inertial")
mi = ET.SubElement(torso, "inertial")
ET.SubElement(mi, "origin", {"xyz": "0 0 0", "rpy": "0 0 0"})
ET.SubElement(mi, "mass", {"value": "1.0"})
ET.SubElement(mi, "inertia", {"ixx": "0.001", "ixy": "0", "ixz": "0",
                              "iyy": "0.001", "iyz": "0", "izz": "0.001"})

def suffix_name(name, sfx):
    return name + sfx if name != "base" else name  # don't suffix the torso

for sfx, sign in (("_l", +1), ("_r", -1)):
    # Duplicate every link with the suffix.
    for link in src_root.findall("link"):
        new_link = ET.SubElement(new_robot, "link", {"name": link.get("name") + sfx})
        for child in link:
            new_link.append(ET.fromstring(ET.tostring(child)))
    # Duplicate every joint with the suffix; rewrite parent/child link refs.
    for joint in src_root.findall("joint"):
        new_joint = ET.SubElement(new_robot, "joint", {
            "name": joint.get("name") + sfx, "type": joint.get("type")})
        for child in joint:
            c = ET.fromstring(ET.tostring(child))
            if c.tag == "parent":
                c.set("link", c.get("link") + sfx)
            elif c.tag == "child":
                c.set("link", c.get("link") + sfx)
            new_joint.append(c)
    # Torso -> dummy_link_{sfx} fixed joint with the lateral offset (positions the arm).
    torso_to_arm = ET.SubElement(new_robot, "joint", {
        "name": f"base_to_{sfx.strip('_')}_arm", "type": "fixed"})
    ET.SubElement(torso_to_arm, "parent", {"link": "base"})
    ET.SubElement(torso_to_arm, "child", {"link": "dummy_link" + sfx})
    ET.SubElement(torso_to_arm, "origin", {"xyz": f"0 {sign * LATERAL} 0", "rpy": "0 0 0"})

ET.ElementTree(new_robot).write(OUT, encoding="utf-8", xml_declaration=True)
print(f"Wrote {OUT}")

# Verify structure
tree2 = ET.parse(OUT)
root2 = tree2.getroot()
links = [l.get("name") for l in root2.findall("link")]
joints = [(j.get("name"), j.get("type")) for j in root2.findall("joint")]
print(f"Links ({len(links)}): {links}")
print(f"Joints ({len(joints)}):")
for n, t in joints:
    print(f"  {n} [{t}]")
# Confirm the cuRobo-critical joints/links exist
need_joints = [f"joint{i}_l" for i in range(1, 7)] + [f"joint{i}_r" for i in range(1, 7)]
have = set(j.get("name") for j in root2.findall("joint"))
missing = [j for j in need_joints if j not in have]
print("Missing cuRobo joints:", missing if missing else "NONE (all joint1_l..joint6_l/r present)")
have_links = set(l.get("name") for l in root2.findall("link"))
print("base_link_l present:", "base_link_l" in have_links)
print("gripper_base_l present:", "gripper_base_l" in have_links)

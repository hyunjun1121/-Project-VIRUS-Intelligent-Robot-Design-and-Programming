# **Project VIRUS: Versatile Intelligent Robotic Unit for Strategy**

## **Overview**

Project VIRUS is an advanced autonomous combat robot developed for the "Intelligent Robot Design and Programming" course (Spring 2025, Grade: A+). This project introduces **VIRUS (Versatile Intelligent Robotic Unit for Strategy)**, a sophisticated robotic system designed to minimize human risk in Close Quarters Battle (CQB) simulations. By integrating a Large Language Model (LLM) with real-time computer vision, VIRUS can understand and execute complex tactical commands, navigate dynamic environments, and engage targets autonomously.

---

## **🎯 Key Features**

* **Natural Language Command Interface**: Operators can issue high-level tactical commands in natural language (e.g., "Clear the hallway and engage any hostiles").  
* **Autonomous Tactical Execution**: The robot can independently perform complex actions such as room clearance, target pursuit, and area reconnaissance.  
* **Real-time Environmental Perception**: Utilizes a suite of sensors and computer vision to detect, identify, and track friendly units and hostile targets.  
* **LLM-Powered Decision Making**: A fine-tuned LLM translates natural language commands into a sequence of executable JSON actions, allowing for dynamic and strategic behavior.  
* **Voice-Synthesized Feedback**: The robot provides real-time audio feedback to the operator, confirming received commands and reporting status updates.

---

## **⚙️ System Architecture & Pipeline**

The VIRUS system is built on a modular pipeline that processes voice commands, perceives the environment, and executes tactical actions.

1. **Voice Command Input**:  
   * **Speech-to-Text**: **OpenAI's Whisper** transcribes the operator's spoken commands into text in real-time.  
2. **Natural Language Understanding (NLU)**:  
   * **Command Interpretation**: A **fine-tuned GPT-4.1-mini model** receives the transcribed text. This model was trained on a custom tactical dataset to accurately interpret ambiguous or complex commands.  
   * **Action Generation**: The LLM converts the command into a structured **JSON format**, defining the specific actions the robot needs to perform (e.g., {"action": "move", "destination": "hallway\_end"}).  
3. **Execution & Control**:  
   * The robot's onboard controller parses the JSON actions and executes the corresponding tactical behaviors, such as navigating to waypoints, scanning for targets, or engaging hostiles.  
4. **Audio Feedback Loop**:  
   * **Text-to-Speech**: **ElevenLabs' API** is used to synthesize the robot's text responses into natural-sounding speech, providing crucial feedback to the human operator.

---

## **🚀 Performance & Results**

The core of this project's success lies in the fine-tuned LLM, which dramatically improved command-following accuracy and tactical effectiveness.

* **Benchmark Performance**: The custom-tuned gpt-4.1-mini model achieved a **70.8% win rate on the AlpacaEval 2.0 benchmark**. This represents a 2x performance increase compared to the baseline, non-tuned model.  
* **Practical Demonstration**: In simulated CQB scenarios, VIRUS successfully executed multi-step commands, demonstrating its ability to clear hallways, pursue designated targets, and adapt to changing environmental inputs.

---

## **🛠️ Technologies Used**

* **Natural Language Processing**: OpenAI GPT-4.1-mini, OpenAI Whisper, ElevenLabs API  
* **Computer Vision**: YOLOv8 (or similar, for object detection)  
* **Robotic Control**: ROS (Robot Operating System)  
* **Programming Languages**: Python

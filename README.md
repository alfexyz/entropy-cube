# 🧊 Entropy Cube Simulation

A 3D interactive simulation that visualizes **entropy** through the motion of particles inside a cube.  
Each subcube is colored according to its **local entropy**, using a blue–red spectrum:
- 🔵 Blue → ordered, low entropy (particles clustered or absent)
- 🔴 Red → disordered, high entropy (particles evenly distributed)

---

## 🎯 Features

- ✅ Realistic 3D particle movement with boundary collisions  
- ✅ Subdivision of the main cube into smaller subcubes  
- ✅ Dynamic color mapping based on **Boltzmann’s entropy formula**  
- ✅ Adjustable particle **count** and **speed** via user interface  
- ✅ Real-time 3D rotation of the cube with mouse control  
- ✅ Semi-transparent entropy field for visual clarity  

---

## ⚙️ Requirements

This project uses **Python 3.10+** and the following libraries:
- PyQt6
- PyOpenGL
- math
- sys
- random

---

## Installing requirements:

```bash
pip install PyQt6 PyOpenGL
```

Optionally, you can use a virtual environment to keep dependencies clean:

```bash
python -m venv entropy_env
source entropy_env/bin/activate  # (on Linux/macOS)
entropy_env\Scripts\activate     # (on Windows)
```

---

## ▶️ How to Run

Run the program from your terminal:

```bash
python main.py
```

Once started:
- Use the **"Particles"** control to change how many particles exist in the cube.  
- Use the **"Speed"** slider to control their movement speed.  
- Click and **drag with the mouse** to rotate the cube in real-time.  

---

## 📊 Entropy Visualization

Each subcube’s color intensity represents **local entropy** according to:

\[
S = -k_B \sum_i p_i \ln(p_i)
\]

Where:
- \(p_i\) = fraction of total particles inside subcube *i*
- \(k_B\) = Boltzmann constant 

Interpretation:
- 🔵 **Low S:** predictable arrangement (particles clustered or missing)
- 🔴 **High S:** random distribution (particles evenly spread)

---

## 💡 Physical Meaning

Entropy measures the **disorder** or **randomness** of a system.  
In this simulation:
- The cube represents a **closed system**.  
- Particles bounce elastically within boundaries.  
- Over time, as particles spread more uniformly, the **average entropy increases**.  

This visually demonstrates the **Second Law of Thermodynamics**:  
> “The entropy of an isolated system tends to increase over time.”

---

## 🧩 Implementation Details

- **Rendering:** done via OpenGL (through PyOpenGL)  
- **Interface:** PyQt6 provides the user interface and OpenGL widget  
- **Physics:** particles have positions (`QVector3D`) and velocities; collisions are handled with vector math  
- **Entropy Calculation:** per-cell counts → probabilities → entropy formula  
- **Color Mapping:** blue-to-red linear interpolation (`_lerp_blue_to_red`)  

---

## 🖼️ Visual Example (to add later)

![Entropy Cube Simulation](video_example/entropy_video.gif)

---


## 👤 Author

**Alex (alfexyz)**  
GitHub: [@alfexyz](https://github.com/alfexyz)

---

## 📄 License

This project is licensed under the **MIT License** —  
you’re free to use, modify, and distribute it, provided credit is given.
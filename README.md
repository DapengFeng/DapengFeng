<p align="right">
  <strong>English</strong> · <a href="README.zh-CN.md">Chinese</a>
</p>

<picture>
  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/profile/hero-dark-mobile.svg">
  <source media="(max-width: 600px) and (prefers-color-scheme: light)" srcset="assets/profile/hero-light-mobile.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/profile/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/profile/hero-light.svg">
  <img src="assets/profile/hero-dark.svg" width="100%" alt="I'm Dapeng Feng. Computer vision, robotics, graphics. Ph.D., Sun Yat-sen University, June 21, 2026. PhD merged. Questions still open.">
</picture>

I build systems that help robots **perceive and reconstruct the world**, and tools that make working with code a little better.

<p>
  <a href="https://dapengfeng.github.io/"><samp>[website]</samp></a> &nbsp;
  <a href="#-ls-projects"><samp>[projects]</samp></a> &nbsp;
  <a href="https://github.com/DapengFeng/DapengFeng/discussions"><samp>[say hello]</samp></a>
</p>

### `$ git log --author=DapengFeng -5`

<!--RECENT_COMMITS:START-->
- `2026-10-13` `DapengFeng/wgpt-community` · [`263d348`](https://github.com/DapengFeng/wgpt-community/commit/263d348c4b1aa4171650542f83575c0e8c13c4fc) — [fix: grant CLA worker permission to comment on pull requests](https://github.com/DapengFeng/wgpt-community/commit/263d348c4b1aa4171650542f83575c0e8c13c4fc)
- `2026-10-13` `DapengFeng/wgpt-community` · [`aa9bb4e`](https://github.com/DapengFeng/wgpt-community/commit/aa9bb4e04e06b9874db151cb364472014ff96df0) — [fix: conform personal invitations and diagnose CLA API failures](https://github.com/DapengFeng/wgpt-community/commit/aa9bb4e04e06b9874db151cb364472014ff96df0)
- `2026-10-13` `DapengFeng/wgpt-community` · [`7c1f1d3`](https://github.com/DapengFeng/wgpt-community/commit/7c1f1d3ee8578563ed9f66e5b65ecd95734bb958) — [feat: gate collaborator invitations on verified CLA signatures](https://github.com/DapengFeng/wgpt-community/commit/7c1f1d3ee8578563ed9f66e5b65ecd95734bb958)
- `2026-10-13` `DapengFeng/wgpt-community` · [`edd991a`](https://github.com/DapengFeng/wgpt-community/commit/edd991ae58602c5ecadf8c4b679d3ea7e0cac76e) — [Initial commit](https://github.com/DapengFeng/wgpt-community/commit/edd991ae58602c5ecadf8c4b679d3ea7e0cac76e)
- `2026-10-12` `DapengFeng/dapengfeng.github.io` · [`89358ab`](https://github.com/DapengFeng/dapengfeng.github.io/commit/89358ab4c9994629d3bdf0c81f9f45972573a6fc) — [feat: add dense and sparse parallel library benchmarks](https://github.com/DapengFeng/dapengfeng.github.io/commit/89358ab4c9994629d3bdf0c81f9f45972573a6fc)

<sub>Dates: UTC+08:00 · Up to 20 recently pushed public repositories scanned · Default branches only.</sub>
<!--RECENT_COMMITS:END-->

<sub>Scheduled refresh: hourly.</sub>

### `$ ls projects/`

<details>
<summary><samp><strong>cartgs/</strong></samp> — 3D Gaussian splatting SLAM · IEEE RA-L</summary>

<br>

**CaRtGS** — Real-time photorealistic SLAM with 3D Gaussian Splatting. Pixels in, a reconstructed world out.

[<samp>[source]</samp>](https://github.com/DapengFeng/cartgs) &nbsp; [<samp>[paper]</samp>](https://arxiv.org/abs/2410.00486) &nbsp; [<samp>[demos]</samp>](https://dapengfeng.github.io/cartgs/)

</details>

<details>
<summary><samp><strong>S3E/</strong></samp> — Collaborative SLAM dataset · IEEE RA-L</summary>

<br>

**S3E** — A multi-robot dataset bringing together LiDAR, stereo cameras, IMU, and UWB. Mapping is a multiplayer problem.

[<samp>[repository]</samp>](https://github.com/DapengFeng/S3E) &nbsp; [<samp>[paper]</samp>](https://arxiv.org/abs/2210.13723) &nbsp; [<samp>[dataset]</samp>](https://dapengfeng.github.io/S3E/)

</details>

<details>
<summary><samp><strong>RustCxx/</strong></samp> — Rust ideas, C++20 syntax</summary>

<br>

**RustCxx** — Rust-style enums, `Result`, and `Option` in a header-only C++20 library. C++ asked for options. I gave it `Option`.

[<samp>[source]</samp>](https://github.com/DapengFeng/RustCxx)

</details>

### `$ cat notes/index`

- [<samp>pytorch-internals/</samp>](https://dapengfeng.github.io/series/pytorch-internals/) — following tensors behind the scenes.
- [<samp>travel-notes/</samp>](https://dapengfeng.github.io/blog/?category=travel) — places, photos, and observations outside the terminal.

<details>
<summary><samp>$ cat profile.json</samp></summary>

<br>

```json
{
  "name": "Dapeng Feng",
  "interests": [
    "Computer vision",
    "Robotics",
    "Computer graphics"
  ],
  "languages": ["Python", "C++"],
  "tools": [
    "PyTorch", "OpenCV", "ROS",
    "Linux", "Git", "CMake", "LaTeX"
  ]
}
```

</details>

<details>
<summary><samp>$ cat education.log</samp></summary>

<br>

- **Ph.D. · Computer Science and Technology**<br>Sun Yat-sen University · 2021 – 2026
- **Master's · Pattern Recognition and Intelligent Systems**<br>Sun Yat-sen University · 2018 – 2021
- **Bachelor's · Computer Science and Technology**<br>Guangdong University of Foreign Studies · 2014 – 2018

</details>

<details>
<summary><samp>$ cat .rubber-duck.log</samp></summary>

<br>

```text
DUCK   What does T_wc map?
ROBOT  Camera -> world.
DUCK   Where is your input point?
ROBOT  World.

[one inverse later]

ROBOT  Oh.
```

</details>

<details>
<summary><samp>$ ./contribution-snake</samp></summary>

<br>

```text
[warn] Something is eating the commits.
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="profile-snake-contrib/github-contribution-grid-snake-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="profile-snake-contrib/github-contribution-grid-snake.svg">
  <img src="profile-snake-contrib/github-contribution-grid-snake.svg" width="100%" alt="An animated snake eating Dapeng Feng's contribution squares.">
</picture>

</details>

---

<samp>dapeng@github:~$</samp> **[say hello](https://github.com/DapengFeng/DapengFeng/discussions)**

A paper question, a strange bug, a half-formed idea — all welcome. Especially if it involves 3D vision, SLAM, robotics, or making developers' lives easier.

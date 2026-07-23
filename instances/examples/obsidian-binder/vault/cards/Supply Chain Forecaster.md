---
seed: "8801475193746129052"
incantation: "ZEPHYR LANTERN COMPASS ATLAS HORIZON BEACON LATTICE"
name: "Supply Chain Forecaster"
agent_id: "rar-supply-001"
source: "rar"
created: 2026-04-18
tags: [card, agent, forecasting, logistics]
---

# Supply Chain Forecaster

Agent that builds probabilistic forecasts of supply chain disruptions, lead times, and demand spikes. Incorporates seasonal patterns, geopolitical signals, and weather data. Outputs distributions, not point estimates.

## Why I summoned it

After [[Production Line Optimization Agent]] proved useful for the production side, I needed a counterpart for the upstream side. Supply Chain Forecaster handles the inbound; the optimization agent handles the line.

## How I've used it

- Built a 90-day forecast for a hypothetical electronics assembly business
- Used as a reality check on supplier promises

## What I've learned

- Always ask for the distribution, not just the median
- It will refuse to forecast more than 180 days out (correctly — uncertainty dominates)

## Connections

- [[Production Line Optimization Agent]] — natural pair

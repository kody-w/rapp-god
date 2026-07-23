# 🎮 RACon — the experience (the grail)

**RACon is what you see. Everything else disappears.**

You get a **cartridge** — a file. You drop it into RACon. Your AI now *has* that app, game, or tool —
with its own space — and you just use it. You never see a port, a process, a protocol, or a line of
code.

That's the whole product. This repo is the **grail**: the frozen north‑star experience the entire
RAPP ecosystem is measured against. If a change makes RACon harder than *"drop in a cartridge, it
works,"* the change is wrong.

## ▶ Run it

**RACon is itself a vrapplication** — it runs in your browser. **[Open RACon →](https://kody-w.github.io/racon/)**
Insert the built‑in 🍳 Cowork Cookbook egg, or drop in any `.egg` cartridge, and it hatches into its
own twin right there. (`index.html` is the console; `manifest.json` declares it.)

## What a user knows (and what they never have to)

Four things, total:

- **RACon** — the console.
- **your brainstem** — your AI, that RACon runs on.
- **the kited twin** — your AI, following you across your devices (and shareable — multiplayer).
- **`.egg` cartridges** — the apps you get and pass around (just call them **eggs**); an egg hatches into your twin.

Everything else — agents, twins, ports, twin‑chat, the registry, the protocols — is the **builder
layer** ("RAPP speak"). Real users never see it; if they have to, that's a bug.

## The user story

> I heard about a little app for my AI. Someone sent me a file — a **cartridge**.
>
> I dropped it into **RACon**. A moment later it was just *there* — my AI could do the new thing,
> and it had its own little world: its own memory, its own space, its own personality. I didn't
> install anything, configure anything, or read any docs. I popped in the cartridge and it worked.
>
> Later I was out, just my phone. I opened RACon on it, pointed the camera at a code on my laptop,
> and there was my app again — the *same* one, still running back home on my main machine, now in my
> hand. I used it on the bus. I handed the code to a friend and suddenly we were both in it, together.
>
> I never learned what a "twin" or a "port" is. I just have cartridges, and they work — at home, on
> the go, and together.

## The three surfaces (all the same cartridge)

- **RACon** — the console on your main device. Drop a cartridge, it runs.
- **vRACon** — the same thing in the browser. No install at all.
- **RACon Kited** — the online layer: take a running cartridge with you across your devices, and play
  **multiplayer**. (See [SPEC.md](SPEC.md) §3.)

## What this repo is

- **[SPEC.md](SPEC.md)** — `racon/1.0`: the experience spec — the promise to the user, the three
  surfaces, RACon Kited, what's guaranteed, and what stays hidden.
- **[GRAIL.md](GRAIL.md)** — why this is the grail and how to honor it.

The cartridge spec underneath: **[rapp-carts](https://github.com/kody-w/rapp-carts)**. The first
cartridge: **[cowork-cookbook-rapp](https://github.com/kody-w/cowork-cookbook-rapp)**.

MIT © Kody Wildfeuer.

"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

const CENTER_LINKS = [
  { href: "/",        label: "Leaderboard" },
  { href: "/matches", label: "Matches" },
  { href: "/history", label: "History" },
];

const RIGHT_LINK = { href: "/j-tracker", label: "J Tracker" };

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ease-out ${
        scrolled
          ? "bg-wc-card/85 backdrop-blur-md py-2 shadow-lg shadow-black/40 border-b border-wc-border/60"
          : "bg-wc-card py-4 shadow-md shadow-black/10 border-b border-transparent"
      }`}
    >
      <div className="mx-auto grid max-w-6xl grid-cols-3 items-center gap-4 px-6">
        <Link
          href="/"
          onClick={() => setOpen(false)}
          className="group flex items-center gap-3 min-w-0"
        >
          <Image
            src="/logo.png"
            alt="FIFA World Cup 2026"
            loading="eager"
            width={55}
            height={55}
            className={`object-contain transition-all duration-300 ease-out will-change-transform group-hover:scale-110 group-hover:-rotate-3 group-hover:drop-shadow-[0_0_10px_rgba(0,200,150,0.55)] shrink-0 ${
              scrolled ? "!w-9 !h-9" : "!w-13 !h-13"
            }`}
          />
          <div className="flex flex-col leading-tight min-w-0">
            <span
              className={`font-bold text-white truncate transition-all duration-300 ${
                scrolled ? "text-sm" : "text-base"
              }`}
            >
              Can Kim beat 5 AI
            </span>
            <span
              className={`text-wc-gold uppercase tracking-widest text-[10px] overflow-hidden transition-all duration-300 ${
                scrolled ? "max-h-0 opacity-0" : "max-h-3 opacity-100"
              }`}
            >
              World Cup 2026
            </span>
          </div>
        </Link>

        {/* Desktop center links */}
        <div className="hidden md:flex items-center justify-center gap-2 text-sm">
          {CENTER_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`rounded-full text-wc-muted hover:text-white transition-all duration-300 ${
                scrolled ? "px-3 py-1.5" : "px-4 py-2"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>

        {/* Desktop right link / Mobile toggle */}
        <div className="flex items-center justify-end">
          <Link
            href={RIGHT_LINK.href}
            className={`hidden md:block rounded-full text-wc-muted hover:text-white transition-all duration-300 ${
              scrolled ? "px-3 py-1.5" : "px-4 py-2"
            }`}
          >
            {RIGHT_LINK.label}
          </Link>
          <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-label="Toggle navigation"
          aria-expanded={open}
          aria-controls="mobile-nav"
          className="md:hidden inline-flex h-9 w-9 shrink-0 flex-col items-center justify-center gap-1.5 rounded-lg text-wc-muted hover:text-white transition-colors"
        >
          <span
            className={`block h-0.5 w-5 bg-current transition-transform duration-300 ${
              open ? "translate-y-2 rotate-45" : ""
            }`}
          />
          <span
            className={`block h-0.5 w-5 bg-current transition-opacity duration-200 ${
              open ? "opacity-0" : ""
            }`}
          />
          <span
            className={`block h-0.5 w-5 bg-current transition-transform duration-300 ${
              open ? "-translate-y-2 -rotate-45" : ""
            }`}
          />
        </button>
        </div>
      </div>

      {/* Mobile menu */}
      <div
        id="mobile-nav"
        className={`md:hidden mx-auto max-w-6xl px-6 overflow-hidden transition-[max-height,opacity] duration-300 ease-out ${
          open ? "max-h-72 opacity-100 mt-3 pb-3" : "max-h-0 opacity-0"
        }`}
      >
        <div className="flex flex-col gap-1 text-sm">
          {[...CENTER_LINKS, RIGHT_LINK].map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="px-4 py-2.5 rounded-lg text-wc-muted hover:text-white hover:bg-wc-blue/30 transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}

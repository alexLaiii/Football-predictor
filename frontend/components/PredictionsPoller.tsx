"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

export default function PredictionsPoller() {
  const router = useRouter();
  const startRef = useRef(Date.now());

  useEffect(() => {
    const id = setInterval(() => {
      if (Date.now() - startRef.current > 180_000) {
        clearInterval(id);
        return;
      }
      router.refresh();
    }, 2000);
    return () => clearInterval(id);
  }, [router]);

  return null;
}

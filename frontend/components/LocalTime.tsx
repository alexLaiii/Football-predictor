"use client";

export default function LocalTime({
  iso,
  options,
}: {
  iso: string;
  options?: Intl.DateTimeFormatOptions;
}) {
  return (
    <time suppressHydrationWarning dateTime={iso}>
      {new Date(iso).toLocaleString(undefined, options)}
    </time>
  );
}

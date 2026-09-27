import type { ReactNode } from "react";

export default function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`signit-card min-w-0 p-4 sm:p-5 ${className}`}>{children}</div>
  );
}

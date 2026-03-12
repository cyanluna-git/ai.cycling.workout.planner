import { cn } from "@/lib/utils";

interface BrandLockupProps {
  className?: string;
  centered?: boolean;
  iconClassName?: string;
  labelClassName?: string;
  textClassName?: string;
  wordmarkClassName?: string;
}

export function BrandLockup({
  className,
  centered = false,
  iconClassName,
  labelClassName,
  textClassName,
  wordmarkClassName,
}: BrandLockupProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 sm:gap-3",
        centered && "justify-center",
        className,
      )}
    >
      <div className="flex shrink-0 items-center gap-2">
        <img
          src="/logo-256.png"
          alt=""
          className={cn("h-8 w-8 object-contain", iconClassName)}
        />
        <span className={cn("font-bold whitespace-nowrap", textClassName)}>AI Coach</span>
      </div>
      <span
        className={cn("hidden h-5 w-px bg-border sm:block", labelClassName)}
        aria-hidden="true"
      />
      <span className="inline-flex shrink-0 items-center rounded-full border border-border/80 bg-white px-2 py-1 shadow-xs">
        <img
          src="/zelia-wordmark.png"
          alt="ZeLia"
          className={cn("h-6 w-auto object-contain", wordmarkClassName)}
        />
      </span>
    </div>
  );
}

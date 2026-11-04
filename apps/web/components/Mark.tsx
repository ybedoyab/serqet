export function Mark({ size = 36 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label="SERQET shield"
    >
      <path
        d="M32 4 54 12v18c0 14-8.8 24.2-22 30C18.8 54.2 10 44 10 30V12L32 4Z"
        fill="#1b3144"
      />
      <path
        d="M32 14c-6 6-8 10-8 16 0 4 2 7 5 9-4 1-7 4-8 8 4-1 8-4 11-8 3 4 7 7 11 8-1-4-4-7-8-8 3-2 5-5 5-9 0-6-2-10-8-16Z"
        fill="#e7d7c8"
      />
      <circle cx="27" cy="28" r="1.4" fill="#1b3144" />
      <circle cx="37" cy="28" r="1.4" fill="#1b3144" />
      <path d="M24 40c3 3 13 3 16 0" fill="none" stroke="#8d4b2a" strokeWidth="1.6" />
    </svg>
  );
}

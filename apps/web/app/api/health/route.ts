export function GET() {
  const commit =
    process.env.VERCEL_GIT_COMMIT_SHA || process.env.NEXT_PUBLIC_COMMIT_SHA || "dev";
  return Response.json({
    ok: true,
    service: "serqet",
    commit,
  });
}

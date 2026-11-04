import Link from "next/link";
import { Mark } from "./Mark";

const LINKS = [
  ["/", "Overview"],
  ["/benchmarks", "Benchmarks"],
  ["/models", "Models"],
  ["/methodology", "Methodology"],
  ["/about", "About"],
];

export function Header() {
  return (
    <header className="site-header">
      <a className="skip-link" href="#content">
        Skip to content
      </a>
      <div className="wrap nav-row">
        <Link className="brand" href="/">
          <Mark />
          SERQET
        </Link>
        <nav aria-label="Primary">
          <div className="nav-links">
            {LINKS.map(([href, label]) => (
              <Link key={href} href={href}>
                {label}
              </Link>
            ))}
          </div>
        </nav>
      </div>
    </header>
  );
}

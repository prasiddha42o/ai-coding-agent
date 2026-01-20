import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const PIPELINE_STAGES = [
  {
    title: "Plan",
    description:
      "Describe a change in plain language. The Planning Agent reads your repository's structure and proposes concrete steps — you approve or reject before anything runs.",
  },
  {
    title: "Generate & Review",
    description:
      "The Code Generation Agent writes the change as a real diff, not a description. The Review Agent checks it for bugs, security issues, and unused code before it touches disk.",
  },
  {
    title: "Test & Commit",
    description:
      "Applied changes are run against your project's own test suite. Only once tests pass does the Git & Session Agent draft a commit message and PR summary for you to finish.",
  },
];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <header className="border-border/60 flex items-center justify-between border-b px-6 py-4">
        <span className="text-sm font-semibold tracking-tight">AI Coding Agent</span>
        <nav className="flex items-center gap-2">
          <Button variant="ghost" size="sm" render={<a href="/login">Sign in</a>} />
          <Button size="sm" render={<a href="/register">Get started</a>} />
        </nav>
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col items-center gap-16 px-6 py-20 text-center">
        <div className="flex flex-col items-center gap-6">
          <h1 className="text-4xl font-bold tracking-tight text-balance sm:text-5xl">
            A coding agent that shows its work
          </h1>
          <p className="text-muted-foreground max-w-2xl text-lg text-balance">
            Import a repository, describe a change in plain language, and review a planned,
            reviewed, and tested diff before a single file is touched. No modification happens
            without your explicit approval.
          </p>
          <div className="flex gap-3">
            <Button size="lg" render={<a href="/register">Import a repository</a>} />
            <Button size="lg" variant="outline" render={<a href="/login">Sign in</a>} />
          </div>
        </div>

        <div className="grid w-full gap-4 text-left sm:grid-cols-3">
          {PIPELINE_STAGES.map((stage, index) => (
            <Card key={stage.title}>
              <CardHeader>
                <CardTitle className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
                  Step {index + 1}
                </CardTitle>
                <CardTitle className="text-base">{stage.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-sm">{stage.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>

      <footer className="border-border/60 text-muted-foreground border-t px-6 py-4 text-center text-xs">
        A portfolio implementation of a multi-agent software engineering assistant.
      </footer>
    </div>
  );
}

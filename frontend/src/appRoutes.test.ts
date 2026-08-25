import { describe, expect, it } from "vitest";
import { APP_PATHS, APP_ROUTES, humanizeRole, humanizeStatus, visibleAppRoutes } from "./appRoutes";

describe("authenticated route registry", () => {
  it("contains unique destinations for every sidebar route", () => {
    const paths = APP_ROUTES.filter((route) => route.sidebar).map((route) => route.path);
    expect(new Set(paths).size).toBe(paths.length);
    expect(paths).toContain(APP_PATHS.dashboard);
    expect(paths).toContain(APP_PATHS.profile);
  });

  it("filters navigation by permission without changing route definitions", () => {
    const studentPaths = visibleAppRoutes(["app.access", "problem.read_public_school", "problem_report.create", "profile.read_own"]).map((route) => route.path);
    expect(studentPaths).toContain(APP_PATHS.problems);
    expect(studentPaths).not.toContain(APP_PATHS.adminMembers);
    expect(studentPaths).not.toContain(APP_PATHS.mentor);
  });

  it("uses human-readable role and status labels", () => {
    expect(humanizeRole("STUDENT_PROJECT_LEADER")).toBe("Student project leader");
    expect(humanizeStatus("SUBMITTED_FOR_REVIEW")).toBe("Awaiting review");
    expect(humanizeRole("STUDENT_PROJECT_LEADER")).not.toContain("_");
  });
});

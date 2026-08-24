import { describe, expect, it } from "vitest";
import { DEFAULT_MEMBER_PATH, safeNext } from "./auth";

describe("safeNext", () => {
  it("accepts only internal app destinations", () => {
    expect(safeNext("/app/problems?from=login")).toBe("/app/problems?from=login");
    expect(safeNext("/app/dashboard")).toBe("/app/dashboard");
  });

  it("rejects external and malformed destinations", () => {
    expect(safeNext("https://example.com")).toBe(DEFAULT_MEMBER_PATH);
    expect(safeNext("//example.com/app")).toBe(DEFAULT_MEMBER_PATH);
    expect(safeNext("/app/\\\\evil")).toBe(DEFAULT_MEMBER_PATH);
    expect(safeNext("not-a-path")).toBe(DEFAULT_MEMBER_PATH);
    expect(safeNext(undefined)).toBe(DEFAULT_MEMBER_PATH);
  });
});

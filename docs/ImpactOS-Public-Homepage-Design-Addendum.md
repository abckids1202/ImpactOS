A public homepage would make ImpactOS feel like an official SPI platform instead of exposing an unfinished internal login screen to every visitor.
The current screen has two immediate problems:
-  Visitors receive no explanation before authentication. 
-  Login is currently broken—the Not Found message likely means the frontend is calling a missing or incorrectly configured authentication endpoint. 
```
/                    Public SPI Impact Lab homepage
/about               Purpose and relationship to SPI
/how-it-works        Problem → research → intervention → impact
/impact              Approved, anonymized impact stories
/privacy             Privacy, safeguarding, and data-use information
/login               Existing SPI member login
/register            Verified member account activation
/invite/:token       Invitation-based registration
/app/*                Protected ImpactOS application
```
Unauthenticated users opening /app/* should be redirected to:
```
/login?next=/app/...
```
Authenticated members visiting / should see Open Dashboard instead of Register.
Left:
-  SPI logo 
- Pilar Impact Lab 
-  Small subtitle: Powered by ImpactOS 
Center:
-  Home 
-  About 
-  How It Works 
-  Impact Stories 
-  Safety & Privacy 
-  FAQ 
Right:
- Member Login 
- Activate Account 
Also include a link back to the [official SPI website](https://sekolah-pilar-indonesia.sch.id/?utm_source=chatgpt.com).
Suggested copy:
Turn student concerns into measurable change.
Pilar Impact Lab helps the SPI community identify meaningful problems, investigate them responsibly, develop practical interventions, and measure what genuinely changed.
Buttons:
- Explore How It Works 
- SPI Member Login 
Use a formal school-oriented visual—not another login card.
Use four simplified stages:
1. Discover — identify and validate a real problem. 
2. Research — investigate it using evidence and responsible methods. 
3. Act — develop and implement an intervention. 
4. Measure — compare results and publish what was learned. 
Separate cards for:
-  Students 
-  Student project leaders 
-  Teachers and mentors 
-  OSIS 
-  School administrators 
Only show school-approved, anonymized results:
-  Problem investigated 
-  Intervention attempted 
-  Observed change 
-  Limitations 
-  Current status 
Never publicly expose reports, student identities, survey responses, internal evidence, or unresolved allegations.
Explain:
-  AI only assists; humans make decisions. 
-  Sensitive reports remain restricted. 
-  Student data is minimized. 
-  ImpactOS is not an emergency-reporting channel. 
-  Results distinguish observed change from proven causation. 
Include:
-  Sekolah Pilar Indonesia 
-  Official school website 
-  Member portal 
-  Privacy 
-  Safeguarding/help information 
-  Contact 
-  Pilot status 
Registration should not be freely open to strangers.
Use one of these controlled methods:
-  Verified SPI school email 
-  Invitation token from an administrator 
-  Student/member ID plus administrator approval 
Rename the public CTA from Register to Activate SPI Account. This makes it clear that only genuine SPI members can join.
Demo accounts and the “switch synthetic demo role” list must appear only in development/demo mode—not on the real public login screen.
```
Modify the existing ImpactOS application to introduce a proper public website
and separate it from the authenticated member application.

Do not rewrite or remove the existing protected application. First inspect the
current route architecture and diagnose the login “Not Found” error. Determine
whether it is caused by an incorrect API base URL, missing /api/v1/auth/login
route, frontend proxy configuration, router fallback, or backend mounting issue.
Fix it and add an integration test before continuing.

Implement:

1. A public route group using PublicLayout:
   /
   /about
   /how-it-works
   /impact
   /privacy
   /faq

2. Authentication routes using AuthLayout:
   /login
   /register
   /invite/:token

3. Move all protected product routes beneath /app:
   /app/dashboard
   /app/problems
   /app/research
   /app/projects
   /app/tasks
   /app/mentor
   /app/osis
   /app/moderation
   /app/admin

4. Redirect unauthenticated access to:
   /login?next=<original-protected-route>

5. After successful login, return the member to the safe validated `next`
   destination or /app/dashboard.

6. The public homepage must include:
   - SPI/Pilar Impact Lab institutional navbar
   - hero section
   - ImpactOS explanation
   - Discover → Research → Act → Measure workflow
   - role-based benefits
   - approved impact-story preview
   - AI and human-governance explanation
   - privacy and safeguarding section
   - FAQ
   - formal footer linking to the official SPI website
   - Member Login and Activate SPI Account CTAs

7. Registration must not be publicly unrestricted. Require either:
   - an approved SPI email domain,
   - a valid invitation token, or
   - administrator approval.

8. Public visitors must never access:
   - internal problem reports,
   - private reports,
   - student identities,
   - survey responses,
   - uploaded evidence,
   - mentor feedback,
   - moderation records,
   - audit logs.

9. Public impact stories must be separately approved, sanitized records—not
   direct views of internal project entities.

10. Hide all demo credentials and role-switching controls unless
    APP_MODE=DEMO and the environment is non-production.

Use ImpactOS’s existing navy/teal design system, but make the public site more
open, institutional, welcoming, and visually rich than the internal dashboard.
Take general inspiration from SPI’s formal school identity while keeping
Pilar Impact Lab visually distinct.

Add frontend tests for public navigation, authenticated navigation, protected
redirects, safe `next` handling, demo-control visibility, and public-data
boundaries. Add backend tests for login, invitation activation, registration
restrictions, and public impact-story serialization.

Finish by running migrations, backend tests, frontend lint/type checks/tests,
and the production build. Report the original login error, its root cause, all
changed routes, completed tests, and remaining limitations.
```
This should be the next development change before expanding the internal modules.
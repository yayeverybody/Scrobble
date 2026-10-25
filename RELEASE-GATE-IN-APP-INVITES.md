# Scrobble release gate — direct invites and multiplayer

This checklist is required before shipping the next iOS release. The static CodeMagic tests alone do not establish device behavior.

## Direct in-app invitations (new work)
- [ ] A signed-in player can search for another existing Scrobble player by display name.
- [ ] The sender can select a matching account without revealing email addresses.
- [ ] The recipient gets an in-app pending invitation with Accept and Decline.
- [ ] Accepting joins **exactly one** game, and declining leaves no playable game.
- [ ] The recipient receives an APNs notification when opted in.
- [ ] Invitations remain visible in-app when push is disabled, delayed, or the app was closed.
- [ ] Duplicate invites, repeated taps, expired invites, self-invites, and unknown usernames are handled safely.
- [ ] Authorization is enforced server-side: only sender/recipient can view or act on their invitation.
- [ ] Shareable Universal Links remain available for people who have not signed up.
- [ ] Recent opponents are offered only from actual previous games, not guessed contacts.

## Multiplayer regression — two physical iPhones
- [ ] Invite via Universal Link with app running and fully closed.
- [ ] Invite via in-app username and accept on the other phone.
- [ ] Turn push received when app backgrounded; opening push navigates to correct game.
- [ ] Nudge succeeds on the opponent's turn and respects cooldown.
- [ ] Both devices show identical board and scores after every move, challenge, swap, and pass.
- [ ] Reopening after force-quit preserves game state and correct turn.
- [ ] Duplicate network responses never duplicate a played move.

## Rules and endgame
- [ ] Classic mode uses ordinary dictionary validation, not the SSA proper-name list.
- [ ] Name Dropper recognizes Sara, Sarah, Josh, Joshua and other SSA names.
- [ ] Unknown proper names still follow the opponent-review path.
- [ ] Crazy Random Bonus Spots, Name Dropper, and Vowels Are Worth Too Much each work alone and together.
- [ ] A/E/I/O/U show and score 20, Y stays normal, and multiplayer endgame deductions use the saved rule.
- [ ] Game ends correctly on last tile played with an empty bag.
- [ ] Game ends correctly after consecutive passes with an empty bag, including CPU games.
- [ ] Final scores and tile deductions are correct and persist after reopening.
- [ ] Rematch retains only intended settings; new game starts with fresh board/racks.
- [ ] Both opening racks contain at least two vowels.

## Release
- [ ] Remove the WEIRD TEST 1.0.50 development overlay.
- [ ] Check splash, sound, haptics, sign-in, account photo and settings.
- [ ] Run CodeMagic build and all automated tests successfully.
- [ ] Test the actual signed TestFlight binary on both phones.
- [ ] Bump app version/build and write release notes.
- [ ] Submit only after the above checks pass.

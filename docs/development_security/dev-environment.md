\# Development Environment Setup



This document describes a \*\*recommended, portable Git setup\*\*

to keep Windows 11 and WSL environments aligned when working

on this repository.



All examples use \*\*placeholders\*\* and are safe to publish.



---



\## Repository



This project uses SSH for Git operations.



Public repository URL:

```

git@github.com:<GITHUB\_USERNAME>/<REPOSITORY\_NAME>.git

```



---



\## Git Transport (SSH)



Always use SSH instead of HTTPS.



```bash

git remote set-url origin git@github.com:<GITHUB\_USERNAME>/<REPOSITORY\_NAME>.git

```



Verify:

```bash

git remote -v

```



---



\## SSH Keys



Recommended key type:



\- \*\*ED25519\*\*

\- One key per machine



The public key must be added to GitHub as:

\- \*\*Authentication key\*\*

\- \*\*Signing key\*\*



Test SSH connectivity:

```bash

ssh -T git@github.com

```



Expected output:

```

Hi <GITHUB\_USERNAME>! You've successfully authenticated...

```



---



\## Commit Signing (SSH-based)



Enable SSH-based commit signing:



```bash

git config --global gpg.format ssh

git config --global user.signingkey ~/.ssh/id\_ed25519.pub

git config --global commit.gpgsign true

```



---



\## allowed\_signers File



Git requires an explicit list of allowed signing keys.



Create the file:



\- \*\*Linux / WSL\*\*

&nbsp; ```

&nbsp; ~/.config/git/allowed\_signers

&nbsp; ```



\- \*\*Windows\*\*



&nbsp; ```

&nbsp; C:/Users/<USERNAME>/.config/git/allowed\_signers

&nbsp; ```



File format (single line per identity):



```

<EMAIL\_OR\_IDENTITY> ssh-ed25519 AAAA...

```



Notes:

\- the SSH key must match `user.signingkey`

\- the file is \*\*personal\*\*

\- it must \*\*not\*\* be committed to the repository



---



\## Signature Verification



Verify commit signatures with:



```bash

git log --show-signature -1

```



Expected result:

```

Good "git" signature for <IDENTITY>

```



---



\## Platform Notes



\- `.gitconfig` may differ between Windows and WSL

\- `allowed\_signers` is local-only

\- only repository policy and hooks should be versioned



---



\## Security Notes



\- Never commit private keys

\- Never commit `allowed\_signers`

\- Do not include personal emails or usernames in documentation

\- Use placeholders in public documentation

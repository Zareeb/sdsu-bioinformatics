# Installing Git
### Windows

```
winget install --id Git.Git -e --source winget
git --version
```
### Mac

```
brew install git
git --version
```
### WSL/Linux

```
sudo apt update
sudo apt install git
git --version
```

# Configure Git identity

```
git config --global user.name "YOUR NAME"
git config --global user.email "123456+username@users.noreply.github.com"
```

Note that if the repository is public, the email you use in your commits is publicly visible. To keep your email private GitHub allows the use of no-reply emails. Go to **Settings** > **Emails** then enable '**Keep my email addresses private'**, and use the provided username@users.noreply.github.com email instead

# SSH setup

## Check for existing keys

`ls ~/.ssh`

Look for **ed25519** and/or **ed25519.pub**

## Generate key if needed

`ssh-keygen -t ed25519 -C "name@example.com"`

## Start SSH agent

### Windows

```
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

### Mac/Linux

```
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

## Copy public key

### Windows

`Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub` 

and copy the output. Alternatively, 

`Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard` 

to automatically add contents to clipboard
### Mac

`cat ~/.ssh/id_ed25519.pub` 

and copy the output. Alternatively, 

`pbcopy < ~/.ssh/id_ed25519.pub` 

to copy directly to clipboard

### Linux

`cat ~/.ssh/id_ed25519.pub` 

and copy the output. Alternatively, use `xsel` if installed, 

`xsel --clipboard < ~/.ssh/id_ed25519.pub`

## Add key to GitHub

Go to Nav menu > **Settings** > **SSH and GPG keys** > **New SSH key** > Paste the key and save

Check connection via 

`ssh -T git@github.com`

type 'yes' if prompted. If successful, you should see an authentication successful message

# GitHub

## Creating a repository

From the nav menu > **Repositories** > **New** >  **repository name** > change visibility as needed and turn '**Add README**' and '**Add .gitignore**' off > **Create repository**

## Clone repository locally

```
git clone git@github.com:USER/repository_name.git
cd repository_name
git status
```

## Add a simple file

Create sample file to commit to the repository

`echo "Hello, World!" >> README.md`

Alternatively, you can follow the example below which does an http-request to retrieve a file

### Windows

```
echo $null >> README.md
Invoke-WebRequest -Uri "https://sdsubioinformatics.org/test_file" -OutFile "README.md"
```

### Mac/Linux

```
touch README.md
wget -O README.md https://sdsubioinformatics.org/test_file
```

## Pushing to GitHub

```
git status
git add README.md
git commit -m "Add README"
git push
```

## Verify file was uploaded on GitHub

You should see a `README.md` file after refreshing your repository.
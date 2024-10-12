---
title: GitHub Workflows
slug: github-workflows
image: unsplash.jpg
date: 2023-08-28
lastmod: 2024-10-12
categories:
  - software
---

A collection of GitHub Actions workflows used by some of my projects.

Many of them rely on reusable workflow files, that are present in this repository ([kuba2k2/kuba2k2](https://github.com/kuba2k2/kuba2k2)). They are designed to be as universal as possible, suitable for most typical projects, as well as some unusual ones.

## Headers

### push.yml

Runs on all pushes (rarely used, in fact - `release` + `push-dev` is a better combo).

```yaml
name: Push, Pull Request
on:
  push:
  pull_request:
```

### push-dev.yml

Runs on all pushes except for releases.

```yaml
name: Push (dev), Pull Request
on:
  push:
    branches: ["**"]
  pull_request:
```

### push-master.yml

Runs on all pushes to master branch.

```yaml
name: Push (master)
on:
  push:
    branches: ["master"]
```

### push-[WHAT].yml

Runs on all pushes affecting a certain path.

```yaml
name: Push ([WHAT])
on:
  push:
    branches: ["master"]
    paths:
      - .github/workflows/push-[WHAT].yml
      - path/that/triggers/it/**
```

### release.yml

Runs on release pushes only.

```yaml
name: Release
on:
  push:
    tags: ["v*.*.*"]
```

### Manual run

Run manually with inputs:

```yaml
name: Manual dispatch
on:
  workflow_dispatch:
    inputs:
      ref:
        description: Upstream ref
        required: false
        default: ''
      version:
        description: Package version
        required: false
        default: ''
```

---

## Common

<details>

Add write permissions for releases:

```yaml
permissions:
  contents: write
```

Checkout repository:

```yaml
      - name: Checkout repository
        uses: actions/checkout@v3
```

Committing changes:

```yaml
      - name: Commit and push changes
        env:
          version: ${{ steps.version.outputs.version }}
        run: |
          git config --global user.email "gh-actions@example.com"
          git config --global user.name "GitHub Actions"
          git add .
          git commit -m "[${{ env.version }}] COMMIT_MESSAGE"
          # CHOOSE ONE
          git tag ${{ env.version }}
          git tag v${{ env.version }}
          git remote set-url origin https://github.com/${{ github.repository }}
          git push --force origin TARGET_BRANCH
          git push --force origin ${{ env.version }}
```

Deploying to GitHub Pages:

```yaml
      - name: Deploy to GitHub Pages
        uses: JamesIves/github-pages-deploy-action@v4
        with:
          folder: web/
          target-folder: /
          force: true
```

Publish release assets:

```yaml
      - name: Add GitHub release assets
        uses: softprops/action-gh-release@v1
        with:
          files: |
            dist/*.exe
```

</details>

Versioning:

```yaml
  version:
    name: Get version numbers
    uses: kuba2k2/kuba2k2/.github/workflows/version.yml@master

  use-version:
    name: Print version numbers
    needs:
      - version
    run: |
      # build date
      echo ${{ needs.version.outputs.now-short }} # 23.8.29
      echo ${{ needs.version.outputs.now-long }} # 2023.8.29
      # last commit date
      echo ${{ needs.version.outputs.git-short }} # 22.7.1
      echo ${{ needs.version.outputs.git-long }} # 2022.7.1
      # current tag name
      echo ${{ needs.version.outputs.tag }} # 1.2.0

      sed -i "s/VERSION/${{ needs.version.outputs.tag }}/g" package.json library.json
      sed -i "s/[0-9]\+\.[0-9]\+\.[0-9]\+/${{ needs.version.outputs.tag }}/g" package.json library.json
```

Publish GitHub release:

```yaml
  gh-release:
    name: Publish GitHub release
    needs:
      - version
      - build-step
    uses: kuba2k2/kuba2k2/.github/workflows/gh-release.yml@master
    permissions:
      contents: write
    with:
      artifact: ${{ needs.build-step.outputs.artifact }}
      name: v${{ needs.version.outputs.git-long }}
```

---

## Python

Setup:

```yaml
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install poetry
        uses: Gr1N/setup-poetry@v8
      - name: Install dependencies
        uses: BSFishy/pip-action@v1
        with:
          packages: |
            autoflake
            black
            isort
```

### push-dev.yml

```yaml
name: Push (dev), Pull Request
on:
  push:
    branches: ["**"]
  pull_request:
jobs:
  lint-python:
    name: Run Python lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-python.yml@master
```

#### push-dev.yml (with tests)

```yaml
name: Push (dev), Pull Request
on:
  push:
    branches: ["**"]
  pull_request:
jobs:
  lint-python:
    name: Run Python lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-python.yml@master
  test-python:
    name: Run Python tests
    uses: kuba2k2/kuba2k2/.github/workflows/test-python.yml@master
    with:
      # extra arguments to "poetry install", defaults to:
      install-args: --with dev --with test
      # extra arguments to "pytest", defaults to empty
      args: ""
```

### release.yml

```yaml
name: Release
on:
  push:
    tags: ["v*.*.*"]
jobs:
  lint-python:
    name: Run Python lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-python.yml@master
  publish-pypi:
    name: Publish PyPI package
    needs:
      - lint-python
    uses: kuba2k2/kuba2k2/.github/workflows/publish-pypi.yml@master
    secrets:
      PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

#### release.yml (with tests)

```yaml
name: Release
on:
  push:
    tags: ["v*.*.*"]
jobs:
  lint-python:
    name: Run Python lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-python.yml@master
  test-python:
    name: Run Python tests
    uses: kuba2k2/kuba2k2/.github/workflows/test-python.yml@master
  publish-pypi:
    name: Publish PyPI package
    needs:
      - lint-python
      - test-python
    uses: kuba2k2/kuba2k2/.github/workflows/publish-pypi.yml@master
    secrets:
      PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

### release.yml (custom build)

```yaml
name: Release
on:
  push:
    tags: ["v*.*.*"]
jobs:
  lint-python:
    name: Run Python lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-python.yml@master
  build-poetry:
    name: Build Python package
    needs:
      - lint-python
    uses: kuba2k2/kuba2k2/.github/workflows/build-poetry.yml@master
    with:
      project-directory: ./path/to/poetry/project/
      args: "--format=wheel" # arguments for 'poetry build'
      pre-build: |
        # steps to run before 'poetry build'
      post-build: |
        # steps to run after 'poetry build'
      files: | # files to upload - relative to repo, not project-directory!
        path/to/poetry/project/dist/*.whl
```

### Setup embedded Python 3.10

(for building PyInstaller packages)

<details>

```yaml
    steps:
      - name: Set up Python Custom
        # Configure embedded Python 3.10 modified to work on Windows 7
        shell: cmd
        run: |
          mkdir python
          pushd python
          certutil -urlcache -split -f https://github.com/kuba2k2/cpython/releases/download/v3.10.0-win7/python-3.10.0-embed-amd64-win7.zip python.zip || exit /b
          tar -xf python.zip || exit /b
          certutil -urlcache -split -f https://bootstrap.pypa.io/get-pip.py get-pip.py || exit /b
          python get-pip.py || exit /b

          pushd Lib
          tar -xf ..\python310.zip || exit /b
          popd

          echo .>python310._pth
          echo Lib>>python310._pth
          echo import site>>python310._pth
          set PATH=%cd%\Scripts;%cd%;%PATH%
          popd

          pip install poetry || exit /b
          pip install .[gui] || exit /b
          move python\python310._pth python\python310._pth_
          pip install pyinstaller || exit /b
          move python\python310._pth_ python\python310._pth
```

</details>

---

## PlatformIO

Setup:

```yaml
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Install PlatformIO
        run: |
          python -m pip install --upgrade pip
          pip install --upgrade platformio
```

### push-dev.yml

```yaml
name: Push (dev), Pull Request
on:
  push:
    branches: ["**"]
  pull_request:
jobs:
  lint-clang:
    name: Run Clang lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-clang.yml@master
```

### release.yml (publish library)

```yaml
name: Release
on:
  push:
    tags: ["v*.*.*"]
jobs:
  lint-clang:
    name: Run Clang lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-clang.yml@master
  publish-pio-library:
    name: Publish PlatformIO library
    needs:
      - lint-clang
    uses: kuba2k2/kuba2k2/.github/workflows/publish-pio-library.yml@master
    secrets:
      PLATFORMIO_AUTH_TOKEN: ${{ secrets.PLATFORMIO_AUTH_TOKEN }}
```

### release.yml (publish platform)

```yaml
name: Release
on:
  push:
    tags: ["v*.*.*"]
jobs:
  lint-clang:
    name: Run Clang lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-clang.yml@master
  publish-pio-platform:
    name: Publish PlatformIO platform
    needs:
      - lint-clang
    uses: kuba2k2/kuba2k2/.github/workflows/publish-pio-platform.yml@master
    secrets:
      PLATFORMIO_AUTH_TOKEN: ${{ secrets.PLATFORMIO_AUTH_TOKEN }}
```

### release.yml (build project)

```yaml
name: Release
on:
  push:
    tags: ["v*.*.*"]
jobs:
  lint-clang:
    name: Run Clang lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-clang.yml@master
  build-pio:
    name: Build PlatformIO project
    needs:
      - lint-clang
    uses: kuba2k2/kuba2k2/.github/workflows/build-pio.yml@master
    with:
      project-directory: ./path/to/platformio/project/
      pre-build: |
        # steps to run before 'pio run'
      post-build: |
        # steps to run after 'pio run', e.g. collecting/renaming binaries
      files: | # files to upload - relative to repo, not project-directory!
        path/to/platformio/project/.pio/build/my-env/program.exe
  gh-release:
    name: Publish GitHub release
    needs:
      - build-pio
    uses: kuba2k2/kuba2k2/.github/workflows/gh-release.yml@master
    permissions:
      contents: write
    with:
      artifact: ${{ needs.build-pio.outputs.artifact }}
```

---

## Node.js / JavaScript

Setup:

```yaml
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 16
```

### push-dev.yml

```yaml
name: Push (dev), Pull Request
on:
  push:
    branches: ["**"]
  pull_request:
jobs:
  lint-node:
    name: Run Node.js lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-node.yml@master
  test-node:
    name: Run Node.js tests
    uses: kuba2k2/kuba2k2/.github/workflows/test-node.yml@master
```

### release.yml (publish library)

```yaml
name: Release
on:
  push:
    tags: ["v*.*.*"]
jobs:
  lint-node:
    name: Run Node.js lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-node.yml@master
  test-node:
    name: Run Node.js tests
    uses: kuba2k2/kuba2k2/.github/workflows/test-node.yml@master
  publish-npm:
    name: Publish NPM package
    needs:
      - lint-node
      - test-node
    uses: kuba2k2/kuba2k2/.github/workflows/publish-npm.yml@master
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### release.yml (build project)

```yaml
name: Release
on:
  push:
    tags: ["v*.*.*"]
jobs:
  lint-node:
    name: Run Node.js lint
    uses: kuba2k2/kuba2k2/.github/workflows/lint-node.yml@master
  test-node:
    name: Run Node.js tests
    uses: kuba2k2/kuba2k2/.github/workflows/test-node.yml@master
  build-node:
    name: Build Node.js project
    needs:
      - lint-node
      - test-node
    uses: kuba2k2/kuba2k2/.github/workflows/build-node.yml@master
    with:
      project-directory: ./path/to/nodejs/package/
      pre-build: |
        # steps to run before 'npm run build'
      post-build: |
        # steps to run after 'npm run build', e.g. collecting/renaming outputs
      files: | # files to upload - relative to repo, not project-directory!
        path/to/nodejs/package/dist/myscript.js
  gh-release:
    name: Publish GitHub release
    needs:
      - build-node
    uses: kuba2k2/kuba2k2/.github/workflows/gh-release.yml@master
    permissions:
      contents: write
    with:
      artifact: ${{ needs.build-node.outputs.artifact }}
```

---

## Windows (NSIS)

```yaml
  build-nsis:
    name: Build NSIS installer
    needs:
      - build-step
    uses: kuba2k2/kuba2k2/.github/workflows/build-nsis.yml@master
    with:
      input-artifact: ${{ needs.build-step.outputs.artifact }}
      input-path: where/to/extract/it/
      script-file: install.nsi
      pre-build: |
        # steps to run before 'makensis'
      post-build: |
        # steps to run after 'makensis', e.g. collecting/renaming binaries
      files: | # files to upload - relative to repo
        my-installer.exe
  gh-release:
    name: Publish GitHub release
    needs:
      - build-nsis
    uses: kuba2k2/kuba2k2/.github/workflows/gh-release.yml@master
    permissions:
      contents: write
    with:
      artifact: ${{ needs.build-nsis.outputs.artifact }}
```

## Alpine Linux

```yaml
name: Release
on:
  push:
    tags: ["v*.*.*"]
jobs:
  abuild:
    name: Build Alpine Linux packages
    uses: kuba2k2/kuba2k2/.github/workflows/abuild.yml@master
    strategy:
      matrix:
        arch:
          - x86
          - x86_64
          - armhf
          - armv7
    secrets:
      ABUILD_KEYNAME: ${{ secrets.ABUILD_KEYNAME }}
      ABUILD_PRIVKEY: ${{ secrets.ABUILD_PRIVKEY }}
      ABUILD_PUBKEY: ${{ secrets.ABUILD_PUBKEY }}
    with:
      project-directory: ./working/directory/for/scripts/
      pre-build: |
        # steps to run before 'build'
      arch: ${{ matrix.arch }}
      branch: latest-stable
      extra-repositories: http://dl-cdn.alpinelinux.org/alpine/edge/testing
      packages: >
        gcc
        python3
        platformio-core
      build: |
        # REQUIRED - commands to build the package(s)
        # Commands are executed as 'actions' user within the Alpine chroot
        cd my-package/
        abuild -r
      post-build: |
        # steps to run after 'build'
      files: | # *extra* files to upload - relative to repo, not project-directory!
        working/directory/for/scripts/my-extra-file.zip
        my-file-2.zip
      deploy: true  # false to skip GitHub Pages deployment with APK repos
  gh-release:
    name: Publish GitHub release
    needs:
      - abuild
    uses: kuba2k2/kuba2k2/.github/workflows/gh-release.yml@master
    permissions:
      contents: write
    with:
      artifact: ${{ needs.abuild.outputs.artifact }}
```

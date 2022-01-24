import { DotGitHub, GH, GitHubEvents, GitHubPaths } from '@gdcorp-im/dotgithub-core'
import { Actions } from '@gdcorp-im/dotgithub-actions'

export default {
    workflows: {
        docs: {
            name: "Build and test documentation",
            on: GitHubEvents.PushAndPullRequest('main', { ...GitHubPaths.OnlyDocs }),
            jobs: {
                build: {
                    name: 'Build Docs',
                    "runs-on": 'ubuntu-latest',
                    steps: [
                        Actions.checkout(),
                        Actions.run('echo ' + GH.secret('NpmToken'))
                    ]
                }
            }
        },
        ci: {
            name: 'Build and test',
            on: GitHubEvents.PushAndPullRequest('main', { ...GitHubPaths.WithoutDocs }),
            jobs: {
                build: {
                    name: 'Build Code',
                    "runs-on": 'ubuntu-latest',
                    steps: [
                        Actions.checkout(),
                        Actions.run('echo ' + GH.secret('NpmToken'))
                    ]
                }
            }
        }
    }
} as DotGitHub

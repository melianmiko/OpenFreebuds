import "scripts/base.just"
import 'scripts/build.just'
import 'scripts/manage/justfile'
import 'scripts/linux/justfile'
import 'scripts/macos/justfile'
import 'scripts/flatpak/justfile'
import 'scripts/windows/justfile'
import 'scripts/ansible/justfile'
import 'scripts/devenv.just'

# List available actions
[private]
@default:
    just -l

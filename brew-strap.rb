## usage: brew install --HEAD <this-raw-url.rb>
## also will need to tap dupes: brew tap homebrew/dupes
## also look at http://lapwinglabs.com/blog/hacker-guide-to-setting-up-your-mac

require "formula"

class BrewStrap < Formula
  homepage "https://github.com/rodolf0/snippets"
  head homepage + '.git'

  # GNU utils make MacOSX feel less like BSD...
  depends_on 'coreutils'
  depends_on 'homebrew/dupes/diffutils'
  depends_on 'moreutils'
  depends_on 'findutils' => '--default-names'
  depends_on 'gawk'
  depends_on 'gnu-indent' => '--default-names'
  depends_on 'gnu-sed' => '--default-names'
  depends_on 'gnu-tar' => '--default-names'
  depends_on 'gnu-which' => '--default-names'
  depends_on 'homebrew/dupes/grep' => '--default-names'
  depends_on 'homebrew/dupes/gzip'
  depends_on 'watch'
  depends_on 'wdiff' => '--with-gettext'
  depends_on 'wget'

  # Thanks for the antiques, MacOSX...
  depends_on 'bash' # use this to change default shell chsh -s /usr/local/bin/bash
  depends_on 'homebrew/dupes/gpatch'
  depends_on 'git'
  depends_on 'homebrew/dupes/less'
  depends_on 'homebrew/dupes/openssh' => '--with-brewed-openssl'
  depends_on 'python' => '--with-brewed-openssl'
  depends_on 'homebrew/dupes/rsync'
  depends_on 'vim' => '--override-system-vi'

  # Misc
  depends_on "mosh"
  depends_on "weechat"

  def install
    opoo 'Enjoy your GNU environment!'
  end
end

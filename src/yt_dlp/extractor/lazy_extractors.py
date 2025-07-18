import importlib
import random
import re

from ..utils import (
    age_restricted,
    bug_reports_message,
    classproperty,
    variadic,
    write_string,
)

# These bloat the lazy_extractors, so allow them to passthrough silently
ALLOWED_CLASSMETHODS = {'extract_from_webpage', 'get_testcases', 'get_webpage_testcases'}
_WARNED = False


class LazyLoadMetaClass(type):
    def __getattr__(cls, name):
        global _WARNED
        if ('_real_class' not in cls.__dict__
                and name not in ALLOWED_CLASSMETHODS and not _WARNED):
            _WARNED = True
            write_string('WARNING: Falling back to normal extractor since lazy extractor '
                         f'{cls.__name__} does not have attribute {name}{bug_reports_message()}\n')
        return getattr(cls.real_class, name)


class LazyLoadExtractor(metaclass=LazyLoadMetaClass):
    @classproperty
    def real_class(cls):
        if '_real_class' not in cls.__dict__:
            cls._real_class = getattr(importlib.import_module(cls._module), cls.__name__)
        return cls._real_class

    def __new__(cls, *args, **kwargs):
        instance = cls.real_class.__new__(cls.real_class)
        instance.__init__(*args, **kwargs)
        return instance

    _module = None
    _ENABLED = True
    _VALID_URL = None
    _WORKING = True
    IE_DESC = None
    _NETRC_MACHINE = None
    SEARCH_KEY = None
    age_limit = 0
    _RETURN_TYPE = None

    @classmethod
    def ie_key(cls):
        """A string for getting the InfoExtractor with get_info_extractor"""
        return cls.__name__[:-2]

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        # This function must import everything it needs (except other extractors),
        # so that lazy_extractors works correctly
        return cls._match_valid_url(url) is not None

    @classmethod
    def _match_valid_url(cls, url):
        if cls._VALID_URL is False:
            return None
        # This does not use has/getattr intentionally - we want to know whether
        # we have cached the regexp for *this* class, whereas getattr would also
        # match the superclass
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = tuple(map(re.compile, variadic(cls._VALID_URL)))
        return next(filter(None, (regex.match(url) for regex in cls._VALID_URL_RE)), None)

    @classmethod
    def working(cls):
        """Getter method for _WORKING."""
        return cls._WORKING

    @classmethod
    def get_temp_id(cls, url):
        try:
            return cls._match_id(url)
        except (IndexError, AttributeError):
            return None

    @classmethod
    def _match_id(cls, url):
        return cls._match_valid_url(url).group('id')

    @classmethod
    def description(cls, *, markdown=True, search_examples=None):
        """Description of the extractor"""
        desc = ''
        if cls._NETRC_MACHINE:
            if markdown:
                desc += f' [*{cls._NETRC_MACHINE}*](## "netrc machine")'
            else:
                desc += f' [{cls._NETRC_MACHINE}]'
        if cls.IE_DESC is False:
            desc += ' [HIDDEN]'
        elif cls.IE_DESC:
            desc += f' {cls.IE_DESC}'
        if cls.SEARCH_KEY:
            desc += f'{";" if cls.IE_DESC else ""} "{cls.SEARCH_KEY}:" prefix'
            if search_examples:
                _COUNTS = ('', '5', '10', 'all')
                desc += f' (e.g. "{cls.SEARCH_KEY}{random.choice(_COUNTS)}:{random.choice(search_examples)}")'
        if not cls.working():
            desc += ' (**Currently broken**)' if markdown else ' (Currently broken)'

        # Escape emojis. Ref: https://github.com/github/markup/issues/1153
        name = (' - **{}**'.format(re.sub(r':(\w+:)', ':\u200B\\g<1>', cls.IE_NAME))) if markdown else cls.IE_NAME
        return f'{name}:{desc}' if desc else name

    @classmethod
    def is_suitable(cls, age_limit):
        """Test whether the extractor is generally suitable for the given age limit"""
        return not age_restricted(cls.age_limit, age_limit)

    @classmethod
    def supports_login(cls):
        return bool(cls._NETRC_MACHINE)

    @classmethod
    def is_single_video(cls, url):
        """Returns whether the URL is of a single video, None if unknown"""
        if cls.suitable(url):
            return {'video': True, 'playlist': False}.get(cls._RETURN_TYPE)


class LazyLoadSearchExtractor(LazyLoadExtractor):
    pass


class YoutubeBaseInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'YoutubeBaseInfoExtract'
    _NETRC_MACHINE = 'youtube'


class YoutubeIE(YoutubeBaseInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube'
    _VALID_URL = '(?x)^\n                     (\n                         (?:https?://|//)                                    # http(s):// or protocol-independent URL\n                         (?:(?:(?:(?:\\w+\\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie|kids)?\\.com|\n                            (?:www\\.)?deturl\\.com/www\\.youtube\\.com|\n                            (?:www\\.)?pwnyoutube\\.com|\n                            (?:www\\.)?hooktube\\.com|\n                            (?:www\\.)?yourepeat\\.com|\n                            tube\\.majestyc\\.net|\n                            (?:www\\.)?redirect\\.invidious\\.io|(?:(?:www|dev)\\.)?invidio\\.us|(?:www\\.)?invidious\\.pussthecat\\.org|(?:www\\.)?invidious\\.zee\\.li|(?:www\\.)?invidious\\.ethibox\\.fr|(?:www\\.)?iv\\.ggtyler\\.dev|(?:www\\.)?inv\\.vern\\.i2p|(?:www\\.)?am74vkcrjp2d5v36lcdqgsj2m6x36tbrkhsruoegwfcizzabnfgf5zyd\\.onion|(?:www\\.)?inv\\.riverside\\.rocks|(?:www\\.)?invidious\\.silur\\.me|(?:www\\.)?inv\\.bp\\.projectsegfau\\.lt|(?:www\\.)?invidious\\.g4c3eya4clenolymqbpgwz3q3tawoxw56yhzk4vugqrl6dtu3ejvhjid\\.onion|(?:www\\.)?invidious\\.slipfox\\.xyz|(?:www\\.)?invidious\\.esmail5pdn24shtvieloeedh7ehz3nrwcdivnfhfcedl7gf4kwddhkqd\\.onion|(?:www\\.)?inv\\.vernccvbvyi5qhfzyqengccj7lkove6bjot2xhh5kajhwvidqafczrad\\.onion|(?:www\\.)?invidious\\.tiekoetter\\.com|(?:www\\.)?iv\\.odysfvr23q5wgt7i456o5t3trw2cw5dgn56vbjfbq2m7xsc5vqbqpcyd\\.onion|(?:www\\.)?invidious\\.nerdvpn\\.de|(?:www\\.)?invidious\\.weblibre\\.org|(?:www\\.)?inv\\.odyssey346\\.dev|(?:www\\.)?invidious\\.dhusch\\.de|(?:www\\.)?iv\\.melmac\\.space|(?:www\\.)?watch\\.thekitty\\.zone|(?:www\\.)?invidious\\.privacydev\\.net|(?:www\\.)?ng27owmagn5amdm7l5s3rsqxwscl5ynppnis5dqcasogkyxcfqn7psid\\.onion|(?:www\\.)?invidious\\.drivet\\.xyz|(?:www\\.)?vid\\.priv\\.au|(?:www\\.)?euxxcnhsynwmfidvhjf6uzptsmh4dipkmgdmcmxxuo7tunp3ad2jrwyd\\.onion|(?:www\\.)?inv\\.vern\\.cc|(?:www\\.)?invidious\\.esmailelbob\\.xyz|(?:www\\.)?invidious\\.sethforprivacy\\.com|(?:www\\.)?yt\\.oelrichsgarcia\\.de|(?:www\\.)?yt\\.artemislena\\.eu|(?:www\\.)?invidious\\.flokinet\\.to|(?:www\\.)?invidious\\.baczek\\.me|(?:www\\.)?y\\.com\\.sb|(?:www\\.)?invidious\\.epicsite\\.xyz|(?:www\\.)?invidious\\.lidarshield\\.cloud|(?:www\\.)?yt\\.funami\\.tech|(?:www\\.)?invidious\\.3o7z6yfxhbw7n3za4rss6l434kmv55cgw2vuziwuigpwegswvwzqipyd\\.onion|(?:www\\.)?osbivz6guyeahrwp2lnwyjk2xos342h4ocsxyqrlaopqjuhwn2djiiyd\\.onion|(?:www\\.)?u2cvlit75owumwpy4dj2hsmvkq7nvrclkpht7xgyye2pyoxhpmclkrad\\.onion|(?:(?:www|no)\\.)?invidiou\\.sh|(?:(?:www|fi)\\.)?invidious\\.snopyta\\.org|(?:www\\.)?invidious\\.kabi\\.tk|(?:www\\.)?invidious\\.mastodon\\.host|(?:www\\.)?invidious\\.zapashcanon\\.fr|(?:www\\.)?(?:invidious(?:-us)?|piped)\\.kavin\\.rocks|(?:www\\.)?invidious\\.tinfoil-hat\\.net|(?:www\\.)?invidious\\.himiko\\.cloud|(?:www\\.)?invidious\\.reallyancient\\.tech|(?:www\\.)?invidious\\.tube|(?:www\\.)?invidiou\\.site|(?:www\\.)?invidious\\.site|(?:www\\.)?invidious\\.xyz|(?:www\\.)?invidious\\.nixnet\\.xyz|(?:www\\.)?invidious\\.048596\\.xyz|(?:www\\.)?invidious\\.drycat\\.fr|(?:www\\.)?inv\\.skyn3t\\.in|(?:www\\.)?tube\\.poal\\.co|(?:www\\.)?tube\\.connect\\.cafe|(?:www\\.)?vid\\.wxzm\\.sx|(?:www\\.)?vid\\.mint\\.lgbt|(?:www\\.)?vid\\.puffyan\\.us|(?:www\\.)?yewtu\\.be|(?:www\\.)?yt\\.elukerio\\.org|(?:www\\.)?yt\\.lelux\\.fi|(?:www\\.)?invidious\\.ggc-project\\.de|(?:www\\.)?yt\\.maisputain\\.ovh|(?:www\\.)?ytprivate\\.com|(?:www\\.)?invidious\\.13ad\\.de|(?:www\\.)?invidious\\.toot\\.koeln|(?:www\\.)?invidious\\.fdn\\.fr|(?:www\\.)?watch\\.nettohikari\\.com|(?:www\\.)?invidious\\.namazso\\.eu|(?:www\\.)?invidious\\.silkky\\.cloud|(?:www\\.)?invidious\\.exonip\\.de|(?:www\\.)?invidious\\.riverside\\.rocks|(?:www\\.)?invidious\\.blamefran\\.net|(?:www\\.)?invidious\\.moomoo\\.de|(?:www\\.)?ytb\\.trom\\.tf|(?:www\\.)?yt\\.cyberhost\\.uk|(?:www\\.)?kgg2m7yk5aybusll\\.onion|(?:www\\.)?qklhadlycap4cnod\\.onion|(?:www\\.)?axqzx4s6s54s32yentfqojs3x5i7faxza6xo3ehd4bzzsg2ii4fv2iid\\.onion|(?:www\\.)?c7hqkpkpemu6e7emz5b4vyz7idjgdvgaaa3dyimmeojqbgpea3xqjoid\\.onion|(?:www\\.)?fz253lmuao3strwbfbmx46yu7acac2jz27iwtorgmbqlkurlclmancad\\.onion|(?:www\\.)?invidious\\.l4qlywnpwqsluw65ts7md3khrivpirse744un3x7mlskqauz5pyuzgqd\\.onion|(?:www\\.)?owxfohz4kjyv25fvlqilyxast7inivgiktls3th44jhk3ej3i7ya\\.b32\\.i2p|(?:www\\.)?4l2dgddgsrkf2ous66i6seeyi6etzfgrue332grh2n7madpwopotugyd\\.onion|(?:www\\.)?w6ijuptxiku4xpnnaetxvnkc5vqcdu7mgns2u77qefoixi63vbvnpnqd\\.onion|(?:www\\.)?kbjggqkzv65ivcqj6bumvp337z6264huv5kpkwuv6gu5yjiskvan7fad\\.onion|(?:www\\.)?grwp24hodrefzvjjuccrkw3mjq4tzhaaq32amf33dzpmuxe7ilepcmad\\.onion|(?:www\\.)?hpniueoejy4opn7bc4ftgazyqjoeqwlvh2uiku2xqku6zpoa4bf5ruid\\.onion|(?:www\\.)?piped\\.kavin\\.rocks|(?:www\\.)?piped\\.tokhmi\\.xyz|(?:www\\.)?piped\\.syncpundit\\.io|(?:www\\.)?piped\\.mha\\.fi|(?:www\\.)?watch\\.whatever\\.social|(?:www\\.)?piped\\.garudalinux\\.org|(?:www\\.)?piped\\.rivo\\.lol|(?:www\\.)?piped-libre\\.kavin\\.rocks|(?:www\\.)?yt\\.jae\\.fi|(?:www\\.)?piped\\.mint\\.lgbt|(?:www\\.)?il\\.ax|(?:www\\.)?piped\\.esmailelbob\\.xyz|(?:www\\.)?piped\\.projectsegfau\\.lt|(?:www\\.)?piped\\.privacydev\\.net|(?:www\\.)?piped\\.palveluntarjoaja\\.eu|(?:www\\.)?piped\\.smnz\\.de|(?:www\\.)?piped\\.adminforge\\.de|(?:www\\.)?watch\\.whatevertinfoil\\.de|(?:www\\.)?piped\\.qdi\\.fi|(?:(?:www|cf)\\.)?piped\\.video|(?:www\\.)?piped\\.aeong\\.one|(?:www\\.)?piped\\.moomoo\\.me|(?:www\\.)?piped\\.chauvet\\.pro|(?:www\\.)?watch\\.leptons\\.xyz|(?:www\\.)?pd\\.vern\\.cc|(?:www\\.)?piped\\.hostux\\.net|(?:www\\.)?piped\\.lunar\\.icu|(?:www\\.)?hyperpipe\\.surge\\.sh|(?:www\\.)?hyperpipe\\.esmailelbob\\.xyz|(?:www\\.)?listen\\.whatever\\.social|(?:www\\.)?music\\.adminforge\\.de|\n                            youtube\\.googleapis\\.com)/                        # the various hostnames, with wildcard subdomains\n                         (?:.*?\\#/)?                                          # handle anchor (#/) redirect urls\n                         (?:                                                  # the various things that can precede the ID:\n                             (?:(?:v|embed|e|shorts|live)/(?!videoseries|live_stream))  # v/ or embed/ or e/ or shorts/\n                             |(?:                                             # or the v= param in all its forms\n                                 (?:(?:watch|movie)(?:_popup)?(?:\\.php)?/?)?  # preceding watch(_popup|.php) or nothing (like /?v=xxxx)\n                                 (?:\\?|\\#!?)                                  # the params delimiter ? or # or #!\n                                 (?:.*?[&;])??                                # any other preceding param (like /?s=tuff&v=xxxx or ?s=tuff&amp;v=V36LpHqtcDY)\n                                 v=\n                             )\n                         ))\n                         |(?:\n                            youtu\\.be|                                        # just youtu.be/xxxx\n                            vid\\.plus|                                        # or vid.plus/xxxx\n                            zwearz\\.com/watch|                                # or zwearz.com/watch/xxxx\n                            (?:www\\.)?redirect\\.invidious\\.io|(?:(?:www|dev)\\.)?invidio\\.us|(?:www\\.)?invidious\\.pussthecat\\.org|(?:www\\.)?invidious\\.zee\\.li|(?:www\\.)?invidious\\.ethibox\\.fr|(?:www\\.)?iv\\.ggtyler\\.dev|(?:www\\.)?inv\\.vern\\.i2p|(?:www\\.)?am74vkcrjp2d5v36lcdqgsj2m6x36tbrkhsruoegwfcizzabnfgf5zyd\\.onion|(?:www\\.)?inv\\.riverside\\.rocks|(?:www\\.)?invidious\\.silur\\.me|(?:www\\.)?inv\\.bp\\.projectsegfau\\.lt|(?:www\\.)?invidious\\.g4c3eya4clenolymqbpgwz3q3tawoxw56yhzk4vugqrl6dtu3ejvhjid\\.onion|(?:www\\.)?invidious\\.slipfox\\.xyz|(?:www\\.)?invidious\\.esmail5pdn24shtvieloeedh7ehz3nrwcdivnfhfcedl7gf4kwddhkqd\\.onion|(?:www\\.)?inv\\.vernccvbvyi5qhfzyqengccj7lkove6bjot2xhh5kajhwvidqafczrad\\.onion|(?:www\\.)?invidious\\.tiekoetter\\.com|(?:www\\.)?iv\\.odysfvr23q5wgt7i456o5t3trw2cw5dgn56vbjfbq2m7xsc5vqbqpcyd\\.onion|(?:www\\.)?invidious\\.nerdvpn\\.de|(?:www\\.)?invidious\\.weblibre\\.org|(?:www\\.)?inv\\.odyssey346\\.dev|(?:www\\.)?invidious\\.dhusch\\.de|(?:www\\.)?iv\\.melmac\\.space|(?:www\\.)?watch\\.thekitty\\.zone|(?:www\\.)?invidious\\.privacydev\\.net|(?:www\\.)?ng27owmagn5amdm7l5s3rsqxwscl5ynppnis5dqcasogkyxcfqn7psid\\.onion|(?:www\\.)?invidious\\.drivet\\.xyz|(?:www\\.)?vid\\.priv\\.au|(?:www\\.)?euxxcnhsynwmfidvhjf6uzptsmh4dipkmgdmcmxxuo7tunp3ad2jrwyd\\.onion|(?:www\\.)?inv\\.vern\\.cc|(?:www\\.)?invidious\\.esmailelbob\\.xyz|(?:www\\.)?invidious\\.sethforprivacy\\.com|(?:www\\.)?yt\\.oelrichsgarcia\\.de|(?:www\\.)?yt\\.artemislena\\.eu|(?:www\\.)?invidious\\.flokinet\\.to|(?:www\\.)?invidious\\.baczek\\.me|(?:www\\.)?y\\.com\\.sb|(?:www\\.)?invidious\\.epicsite\\.xyz|(?:www\\.)?invidious\\.lidarshield\\.cloud|(?:www\\.)?yt\\.funami\\.tech|(?:www\\.)?invidious\\.3o7z6yfxhbw7n3za4rss6l434kmv55cgw2vuziwuigpwegswvwzqipyd\\.onion|(?:www\\.)?osbivz6guyeahrwp2lnwyjk2xos342h4ocsxyqrlaopqjuhwn2djiiyd\\.onion|(?:www\\.)?u2cvlit75owumwpy4dj2hsmvkq7nvrclkpht7xgyye2pyoxhpmclkrad\\.onion|(?:(?:www|no)\\.)?invidiou\\.sh|(?:(?:www|fi)\\.)?invidious\\.snopyta\\.org|(?:www\\.)?invidious\\.kabi\\.tk|(?:www\\.)?invidious\\.mastodon\\.host|(?:www\\.)?invidious\\.zapashcanon\\.fr|(?:www\\.)?(?:invidious(?:-us)?|piped)\\.kavin\\.rocks|(?:www\\.)?invidious\\.tinfoil-hat\\.net|(?:www\\.)?invidious\\.himiko\\.cloud|(?:www\\.)?invidious\\.reallyancient\\.tech|(?:www\\.)?invidious\\.tube|(?:www\\.)?invidiou\\.site|(?:www\\.)?invidious\\.site|(?:www\\.)?invidious\\.xyz|(?:www\\.)?invidious\\.nixnet\\.xyz|(?:www\\.)?invidious\\.048596\\.xyz|(?:www\\.)?invidious\\.drycat\\.fr|(?:www\\.)?inv\\.skyn3t\\.in|(?:www\\.)?tube\\.poal\\.co|(?:www\\.)?tube\\.connect\\.cafe|(?:www\\.)?vid\\.wxzm\\.sx|(?:www\\.)?vid\\.mint\\.lgbt|(?:www\\.)?vid\\.puffyan\\.us|(?:www\\.)?yewtu\\.be|(?:www\\.)?yt\\.elukerio\\.org|(?:www\\.)?yt\\.lelux\\.fi|(?:www\\.)?invidious\\.ggc-project\\.de|(?:www\\.)?yt\\.maisputain\\.ovh|(?:www\\.)?ytprivate\\.com|(?:www\\.)?invidious\\.13ad\\.de|(?:www\\.)?invidious\\.toot\\.koeln|(?:www\\.)?invidious\\.fdn\\.fr|(?:www\\.)?watch\\.nettohikari\\.com|(?:www\\.)?invidious\\.namazso\\.eu|(?:www\\.)?invidious\\.silkky\\.cloud|(?:www\\.)?invidious\\.exonip\\.de|(?:www\\.)?invidious\\.riverside\\.rocks|(?:www\\.)?invidious\\.blamefran\\.net|(?:www\\.)?invidious\\.moomoo\\.de|(?:www\\.)?ytb\\.trom\\.tf|(?:www\\.)?yt\\.cyberhost\\.uk|(?:www\\.)?kgg2m7yk5aybusll\\.onion|(?:www\\.)?qklhadlycap4cnod\\.onion|(?:www\\.)?axqzx4s6s54s32yentfqojs3x5i7faxza6xo3ehd4bzzsg2ii4fv2iid\\.onion|(?:www\\.)?c7hqkpkpemu6e7emz5b4vyz7idjgdvgaaa3dyimmeojqbgpea3xqjoid\\.onion|(?:www\\.)?fz253lmuao3strwbfbmx46yu7acac2jz27iwtorgmbqlkurlclmancad\\.onion|(?:www\\.)?invidious\\.l4qlywnpwqsluw65ts7md3khrivpirse744un3x7mlskqauz5pyuzgqd\\.onion|(?:www\\.)?owxfohz4kjyv25fvlqilyxast7inivgiktls3th44jhk3ej3i7ya\\.b32\\.i2p|(?:www\\.)?4l2dgddgsrkf2ous66i6seeyi6etzfgrue332grh2n7madpwopotugyd\\.onion|(?:www\\.)?w6ijuptxiku4xpnnaetxvnkc5vqcdu7mgns2u77qefoixi63vbvnpnqd\\.onion|(?:www\\.)?kbjggqkzv65ivcqj6bumvp337z6264huv5kpkwuv6gu5yjiskvan7fad\\.onion|(?:www\\.)?grwp24hodrefzvjjuccrkw3mjq4tzhaaq32amf33dzpmuxe7ilepcmad\\.onion|(?:www\\.)?hpniueoejy4opn7bc4ftgazyqjoeqwlvh2uiku2xqku6zpoa4bf5ruid\\.onion|(?:www\\.)?piped\\.kavin\\.rocks|(?:www\\.)?piped\\.tokhmi\\.xyz|(?:www\\.)?piped\\.syncpundit\\.io|(?:www\\.)?piped\\.mha\\.fi|(?:www\\.)?watch\\.whatever\\.social|(?:www\\.)?piped\\.garudalinux\\.org|(?:www\\.)?piped\\.rivo\\.lol|(?:www\\.)?piped-libre\\.kavin\\.rocks|(?:www\\.)?yt\\.jae\\.fi|(?:www\\.)?piped\\.mint\\.lgbt|(?:www\\.)?il\\.ax|(?:www\\.)?piped\\.esmailelbob\\.xyz|(?:www\\.)?piped\\.projectsegfau\\.lt|(?:www\\.)?piped\\.privacydev\\.net|(?:www\\.)?piped\\.palveluntarjoaja\\.eu|(?:www\\.)?piped\\.smnz\\.de|(?:www\\.)?piped\\.adminforge\\.de|(?:www\\.)?watch\\.whatevertinfoil\\.de|(?:www\\.)?piped\\.qdi\\.fi|(?:(?:www|cf)\\.)?piped\\.video|(?:www\\.)?piped\\.aeong\\.one|(?:www\\.)?piped\\.moomoo\\.me|(?:www\\.)?piped\\.chauvet\\.pro|(?:www\\.)?watch\\.leptons\\.xyz|(?:www\\.)?pd\\.vern\\.cc|(?:www\\.)?piped\\.hostux\\.net|(?:www\\.)?piped\\.lunar\\.icu|(?:www\\.)?hyperpipe\\.surge\\.sh|(?:www\\.)?hyperpipe\\.esmailelbob\\.xyz|(?:www\\.)?listen\\.whatever\\.social|(?:www\\.)?music\\.adminforge\\.de\n                         )/\n                         |(?:www\\.)?cleanvideosearch\\.com/media/action/yt/watch\\?videoId=\n                         )\n                     )?                                                       # all until now is optional -> you can pass the naked ID\n                     (?P<id>[0-9A-Za-z_-]{11})                              # here is it! the YouTube video ID\n                     (?(1).+)?                                                # if we found the ID, everything can follow\n                     (?:\\#|$)'
    IE_DESC = 'YouTube'
    _NETRC_MACHINE = 'youtube'
    age_limit = 18
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        from ..utils import parse_qs

        qs = parse_qs(url)
        if qs.get('list', [None])[0]:
            return False
        return super().suitable(url)


_ALL_CLASSES = [YoutubeIE]
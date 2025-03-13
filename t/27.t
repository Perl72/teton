#!/usr/bin/perl

use strict;
use warnings;
use Test::More;
use File::Spec;
use FindBin;
use Cwd 'abs_path';
use Log::Log4perl;
use File::Path 'make_path';
use Acme::Frobnitz;

# Set up logging
my $log_dir = File::Spec->catdir($FindBin::Bin, '..', 'logs');
my $log_file = File::Spec->catfile($log_dir, 'acme-frobnitz.log');

unless (-d $log_dir) {
    eval { make_path($log_dir) };
    die "Failed to create log directory $log_dir: $@" if $@;
}

my $log_config = qq(
log4perl.logger = INFO, FileAppender
log4perl.appender.FileAppender = Log::Log4perl::Appender::File
log4perl.appender.FileAppender.filename = $log_file
log4perl.appender.FileAppender.layout = Log::Log4perl::Layout::PatternLayout
log4perl.appender.FileAppender.layout.ConversionPattern = %d [%p] %m%n
);
Log::Log4perl->init(\$log_config);
my $logger = Log::Log4perl->get_logger();

# Instantiate Frobnitz object
my $frobnitz = Acme::Frobnitz->new();

# Define list of URLs
my @video_urls = (
    'https://www.instagram.com/p/DHErSwNhaXp/',
    'https://www.instagram.com/p/DHAO0n5tTG0/',
    'https://www.instagram.com/p/DG_vXnIsb-y/', # intelligence unit
    'https://www.instagram.com/p/DG_jfH8xSdP/',
    'https://www.instagram.com/p/DG-_j27R6yb/?img_index=1',
    'https://www.instagram.com/p/DG9hR9CshKQ/?img_index=1',
    'https://www.instagram.com/p/DG8g_tORkIB/',
    'https://www.instagram.com/p/DG6idPgvTH_/',
    'https://www.instagram.com/p/DG1iySAMuSB/',
    'https://www.instagram.com/p/DGuexsmszBD/',
    'https://www.instagram.com/p/DGuel9ksMZi/',
    'https://www.instagram.com/p/DGs7QBUgv6Q/?img_index=1', # Aerial Rec
    'https://www.instagram.com/p/DGqxZQAR7i2/?img_index=1',
    'https://www.instagram.com/p/DGqwcWKx4uP/',
    'https://www.instagram.com/p/DGpNctHt6v5/',
    'https://www.instagram.com/p/DGkw8jaxgeb/',
    'https://www.instagram.com/p/DGjJ_-eRGDb/',
    'https://www.instagram.com/p/DGeg-QuJPeA/',
    'https://www.instagram.com/p/DGdjlNIxbsD/',
    'https://www.instagram.com/p/DGdYFvARfUY/',
    'https://www.instagram.com/p/DGbmXxxhE-b/',
    'https://www.instagram.com/p/DGZc1l4s0nB/',
    'https://www.instagram.com/p/DGZIbBpBhXf/',
    'https://www.instagram.com/p/DGYywtFy9qH/',
    'https://www.instagram.com/reel/DGkw8jaxgeb/',
    'https://www.instagram.com/reel/DGqwcWKx4uP/',
    'https://www.instagram.com/p/DGTZ0KXRsFb/',
    'https://www.instagram.com/p/DGJ8qN2s2ys/',
    '#mar12', # Ignore this non-URL entry
);

# Process each video URL
foreach my $video_url (@video_urls) {
    next if $video_url =~ /^#/;  # Skip comments

    $logger->info("Starting processing for URL: $video_url");

    my $download_output = eval { $frobnitz->call_main($video_url) };

    if ($@) {
        $logger->error("Error calling main.py for $video_url: $@");
        fail("Execution of main.py failed for $video_url");
        next;
    }

    unless ($download_output) {
        $logger->error("No output received from main.py for $video_url");
        fail("No output from main.py for $video_url");
        next;
    }

    my ($last_line) = (split /\n/, $download_output)[-1] // '';
    chomp($last_line) if defined $last_line;

    if ($last_line) {
        ok($last_line, "Processing completed for $video_url: $last_line");
        $logger->info("Processing output: $last_line");
    } else {
        fail("Processing failed for $video_url");
        $logger->error("Processing failed for $video_url");
    }
}

done_testing();


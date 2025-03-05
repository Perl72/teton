#!/usr/bin/perl

# timmy insta reel urls in last 2 weeks...currently 03-05-25

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

# Define list of URLs (from your clips/1.timmy.txt)
my @video_urls = (
    'https://www.instagram.com/reel/DETfEU0MPr9/',
    'https://www.instagram.com/reel/DFy5m4MotA5/',
    'https://www.instagram.com/reel/DGBs4YmSXpj/',
    'https://www.instagram.com/reel/DGJ8qN2s2ys/',
    'https://www.instagram.com/reel/DGTZ0KXRsFb/',
    'https://www.instagram.com/reel/DGYywtFy9qH/',
    'https://www.instagram.com/reel/DGZIbBpBhXf/',
    'https://www.instagram.com/reel/DGZc1l4s0nB/',
    'https://www.instagram.com/reel/DGbmXxxhE-b/',
    'https://www.instagram.com/reel/DGdYFvARfUY/',
    'https://www.instagram.com/reel/DGdjlNIxbsD/',
    'https://www.instagram.com/reel/DGeg-QuJPeA/',
    'https://www.instagram.com/reel/DGjJ_-eRGDb/',
    'https://www.instagram.com/reel/DGkw8jaxgeb/',
    'https://www.instagram.com/reel/DGqwcWKx4uP/',
);

# Process each video URL
foreach my $video_url (@video_urls) {
    $logger->info("Starting download for URL: $video_url");
    my $download_output = $frobnitz->download($video_url);
    my ($last_line) = (split /\n/, $download_output)[-1];
    chomp($last_line);

    ok($last_line, "Download completed for $video_url: $last_line");
    $logger->info("Downloaded video to: $last_line");

    # Verify download
    if ($frobnitz->verify_file($last_line)) {
        pass("File verification successful for $video_url");
        $logger->info("File verification successful for $video_url");
    } else {
        fail("File verification failed for $video_url");
        $logger->error("File verification failed for $video_url");
        BAIL_OUT("Verification failed for $video_url, stopping test.");
    }

    # Add watermark
    $download_output = $frobnitz->add_watermark($last_line);
    ($last_line) = (split /\n/, $download_output)[-1];
    chomp($last_line);
    ok($last_line, "Watermark added for $video_url: $last_line");
    $logger->info("Watermark added to: $last_line");

    # Make clips
    $download_output = $frobnitz->make_clips($last_line);
    ($last_line) = (split /\n/, $download_output)[-1];
    chomp($last_line);
    ok($last_line, "Clips created for $video_url: $last_line");
    $logger->info("Clips created for: $last_line");
}

done_testing();


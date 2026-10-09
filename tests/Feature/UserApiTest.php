<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class UserApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_users_are_returned_in_pages(): void
    {
        User::factory()->count(3)->create();

        $response = $this->getJson('/api/users?per_page=2');

        $response->assertOk()
            ->assertJsonPath('current_page', 1)
            ->assertJsonPath('per_page', 2)
            ->assertJsonCount(2, 'data');
    }

    public function test_page_size_cannot_be_greater_than_two_hundred(): void
    {
        $this->getJson('/api/users?per_page=201')
            ->assertStatus(422)
            ->assertJsonValidationErrors(['per_page']);
    }

    public function test_emails_endpoint_only_returns_email_fields(): void
    {
        User::factory()->create();

        $response = $this->getJson('/api/users/emails');

        $response->assertOk()
            ->assertJsonStructure(['data' => [['id', 'email']]])
            ->assertJsonMissing(['password']);
    }

    public function test_over_twenty_filters_in_the_database_before_pagination(): void
    {
        User::factory()->create(['birth_date' => now()->subYears(30)]);
        User::factory()->create(['birth_date' => now()->subYears(18)]);

        $response = $this->getJson('/api/users/over-twenty?per_page=1');

        $response->assertOk()
            ->assertJsonStructure([
                'cutoff_date',
                'users' => ['data', 'current_page', 'per_page'],
            ])
            ->assertJsonCount(1, 'users.data');
    }
}
